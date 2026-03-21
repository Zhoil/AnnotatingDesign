import re
import io
import jieba
import jieba.analyse
from difflib import SequenceMatcher
from llm_service import LLMService
import fitz  # PyMuPDF - 合并 PDF 覆盖层
import pdfplumber  # 字符级精确文本定位
import os
from docx import Document
from docx.enum.text import WD_COLOR_INDEX

class TextAnalyzer:
    """文本分析器，提取关键点、生成摘要和统计信息"""
    
    def __init__(self):
        # 初始化jieba
        jieba.setLogLevel(jieba.logging.INFO)
        # 初始化大模型LLM服务
        self.llm_service = LLMService()
        # 存储结构化数据（用于精准定位）
        self.current_structured_data = None
        print("LLM 服务已启用（DeepSeek-R1 / Qwen3.5-Plus）")
    
    def analyze(self, text, structured_data=None, api_provider='deepseek'):
        """
        分析文本，返回完整的分析结果
            
        Args:
            text: 待分析文本
            structured_data: 结构化数据（包含 PDF 的图片、表格、文件路径等信息）
            api_provider: API 提供商 ('deepseek' | 'qwen')
        """
        # 保存结构化数据
        self.current_structured_data = structured_data

        print(f"使用 {api_provider} 大模型API进行文本分析...")

        # 获取PDF路径和文件大小
        pdf_path = structured_data.get('filepath') if structured_data else None
        file_size = structured_data.get('file_size', 0) if structured_data else 0

        # 如果有结构化数据，在提示词中添加额外信息
        extra_context = ""
        if structured_data and structured_data.get('structured_content'):
            sc = structured_data['structured_content']
            table_count = len([x for x in sc if x['type'] == 'table'])
            image_count = len([x for x in sc if x['type'] == 'image'])

            if table_count > 0 or image_count > 0:
                extra_context = f"\n\n[文档结构信息] 此文档包含 {table_count} 个表格和 {image_count} 张图片，请结合这些结构化内容进行分析。"

        # 调用大模型
        llm_result = self.llm_service.analyze_text(
            text + extra_context,
            provider=api_provider,
            pdf_path=pdf_path,
            file_size=file_size
        )

        if llm_result:
            return self._process_llm_result(text, llm_result)

        print("大模型分析失败，回退到传统方法")
        return self._traditional_analyze(text)
    
    def _traditional_analyze(self, text):
        """简单传统分析（降级方案）"""
        sentences = self._split_sentences(text)
        title = self._extract_title(sentences)
            
        # 简单选取前 5 句作为关键点
        keypoints = []
        for i, s in enumerate(sentences[:5]):
            keypoints.append({
                'id': i + 1,
                'content': s,
                'summary': s[:20],
                'importance': 70,
                'category': '重点内容',
                'position': i,
                'annotation': '自动提取的关键句',
                'color': '#ffd43b'
            })
                
        summary = {'core_points': [s for s in sentences[:3]], 'key_data': [], 'conclusions': []}
        statistics = self._generate_statistics(text, keypoints)
        highlights = self._generate_highlights(text, keypoints)
            
        return {
            'title': title,
            'keypoints': keypoints,
            'summary': summary,
            'statistics': statistics,
            'highlights': highlights
        }
    
    def _process_llm_result(self, text, llm_result):
        title = llm_result.get('title', '分析报告')
        
        raw_llm_keypoints = []
        for idx, arg in enumerate(llm_result.get('core_arguments', [])):
            point_text  = arg.get('point', '')
            evidence_list = arg.get('evidence', [])
            importance  = arg.get('importance', 95)
            point_page  = arg.get('point_page')
            point_ctx   = arg.get('point_context', '')   # 新字段：上下文句子帮助定位
            ann_label   = arg.get('annotation_label', '\u6838心论点')  # 新字段：边注标签

            # evidence 字符串展示（兼容旧格式）
            evidence_texts = []
            for ev in evidence_list:
                if isinstance(ev, dict):
                    evidence_texts.append(ev.get('text', ''))
                else:
                    evidence_texts.append(str(ev))

            evidence_str = "\n".join([f"• {ev}" for ev in evidence_texts])
            point_annotation = f"【{ann_label}】\n{point_text}\n\n【支撑论据】\n{evidence_str}"

            point_id = (idx + 1) * 100
            raw_llm_keypoints.append({
                'id':          point_id,
                'content':     point_text,
                'context':     point_ctx,       # 上下文传递给定位工具
                'category':    '核心论点',
                'importance':  importance,
                'annotation':  point_annotation,
                'fixed_color': '#ff6b6b',
                'page':        point_page,
            })

            # 每个论据独立高亮
            for e_idx, ev in enumerate(evidence_list):
                if isinstance(ev, dict):
                    ev_text = ev.get('text', '')
                    ev_page = ev.get('page')
                    ev_ctx  = ev.get('context', '')
                else:
                    ev_text = str(ev)
                    ev_page = None
                    ev_ctx  = ''

                raw_llm_keypoints.append({
                    'id':          point_id + e_idx + 1,
                    'content':     ev_text,
                    'context':     ev_ctx,
                    'category':    '支撑论据',
                    'importance':  max(30, importance - 40),
                    'annotation':  f"【支撑论据】针对论点：{point_text[:30]}...",
                    'fixed_color': '#51cf66',
                    'page':        ev_page,
                })
        
        # 匹配到原文
        matched_keypoints = self._match_keypoints_to_text(text, raw_llm_keypoints)
        
        summary = {
            'core_points': [arg.get('point', '') for arg in llm_result.get('core_arguments', [])],
            'key_data': [],
            'conclusions': [llm_result.get('summary', '')]
        }
        
        statistics = self._generate_statistics(text, matched_keypoints)
        highlights = self._generate_highlights(text, matched_keypoints)
        
        return {
            'title': title,
            'keypoints': matched_keypoints,
            'summary': summary,
            'statistics': statistics,
            'highlights': highlights
        }
    
    def _match_keypoints_to_text(self, text, llm_keypoints):
        """
        将大模型提取的关键点匹配到原文中
        对于PDF，使用页码信息进行精准定位
        """
        matched_keypoints = []
        sentences = self._split_sentences(text)
        
        # 获取PDF路径（如果有）
        pdf_path = None
        if self.current_structured_data and self.current_structured_data.get('filepath'):
            filepath = self.current_structured_data['filepath']
            if filepath.lower().endswith('.pdf'):
                pdf_path = filepath
        
        for idx, llm_kp in enumerate(llm_keypoints):
            kp_content = llm_kp.get('content', '')
            kp_page = llm_kp.get('page')  # 获取页码提示
            
            # 方法1：PDF精准定位 - 如果有PDF路径和页码信息
            matched_text = None
            match_method = 'unknown'
            pdf_location = None
            
            if pdf_path and kp_page:
                pdf_location = self._locate_text_in_pdf(pdf_path, kp_content, kp_page)
                if pdf_location:
                    matched_text = kp_content
                    match_method = 'pdf_location'
            
            # 方法2：精确匹配 - 直接在原文中查找
            if not matched_text and kp_content in text:
                matched_text = kp_content
                match_method = 'exact'
            
            # 方法3：模糊匹配 - 找到最相似的句子
            if not matched_text:
                matched_text, match_method = self._fuzzy_match_sentence(kp_content, sentences)
            
            if matched_text:
                # 使用传入的 annotation
                final_annotation = llm_kp.get('annotation', '')
                
                # 生成摘要描述
                point_summary = matched_text[:30] + '...'
                
                # 优先使用 fixed_color，否则根据重要性动态生成
                final_color = llm_kp.get('fixed_color') or self._get_color_by_importance(llm_kp.get('importance', 70) / 100)
                
                keypoint = {
                    'id': llm_kp.get('id') or (idx + 1),
                    'content': matched_text,
                    'llm_content': kp_content,
                    'summary': point_summary,
                    'importance': llm_kp.get('importance', 70),
                    'category': llm_kp.get('category', '核心内容'),
                    'position': sentences.index(matched_text) if matched_text in sentences else -1,
                    'annotation': final_annotation,
                    'color': final_color,
                    'match_method': match_method,
                    'page': kp_page,  # 添加页码信息
                    'pdf_location': pdf_location  # PDF定位信息 (page_num, bbox)
                }
                matched_keypoints.append(keypoint)
        
        # 按重要性排序
        matched_keypoints.sort(key=lambda x: x['importance'], reverse=True)
        
        return matched_keypoints
    
    def _fuzzy_match_sentence(self, target_sentence, sentences):
        """
        模糊匹配句子：从原文句子中找到与目标句子最相似的
        使用多种策略：
        1. 序列相似度
        2. 关键词重叠度
        3. 长度相似度
        """
        if not sentences:
            return target_sentence, 'none'
        
        best_match = None
        best_score = 0.0
        match_method = 'fuzzy'
        
        # 提取目标句子的关键词
        target_keywords = set(jieba.cut(target_sentence))
        
        for sentence in sentences:
            # 计算多个相似度指标
            
            # 1. 序列相似度（SequenceMatcher）
            seq_similarity = SequenceMatcher(None, target_sentence, sentence).ratio()
            
            # 2. 关键词重叠度
            sent_keywords = set(jieba.cut(sentence))
            if len(target_keywords) > 0:
                keyword_overlap = len(target_keywords & sent_keywords) / len(target_keywords)
            else:
                keyword_overlap = 0
            
            # 3. 长度相似度
            len_similarity = 1 - abs(len(target_sentence) - len(sentence)) / max(len(target_sentence), len(sentence))
            
            # 综合评分（加权平均）
            score = seq_similarity * 0.4 + keyword_overlap * 0.4 + len_similarity * 0.2
            
            if score > best_score:
                best_score = score
                best_match = sentence
        
        # 如果相似度较高，返回匹配结果；否则返回原句
        if best_score > 0.5:  # 阈值可调整
            return best_match, match_method
        else:
            # 如果没有好的匹配，尝试部分匹配
            for sentence in sentences:
                if any(keyword in sentence for keyword in target_keywords if len(keyword) > 1):
                    return sentence, 'partial'
            
            # 实在找不到，返回原句
            return target_sentence, 'none'
    
    def _split_sentences(self, text):
        """分句"""
        # 按标点符号分句
        sentences = re.split(r'[。！？\n]+|[.!?]+\s', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        return sentences
    
    def _extract_title(self, sentences):
        """提取标题（第一句或最短的句子）"""
        if not sentences:
            return "未命名文档"
        
        # 如果第一句较短，作为标题
        if len(sentences[0]) < 50:
            return sentences[0]
        
        # 否则找最短的句子
        short_sentences = [s for s in sentences[:5] if len(s) < 50]
        if short_sentences:
            return short_sentences[0]
        
        return sentences[0][:50] + "..."
    
    def _get_color_by_importance(self, score):
        """根据重要性返回颜色"""
        if score >= 0.7:
            return '#ff6b6b'  # 红色 - 极其重要
        elif score >= 0.5:
            return '#ffa94d'  # 橙色 - 很重要
        elif score >= 0.3:
            return '#ffd43b'  # 黄色 - 重要
        else:
            return '#74c0fc'  # 蓝色 - 一般重要
    
    def _generate_statistics(self, text, keypoints):
        """生成文本统计信息"""
        word_count = len(text)
        keypoint_count = len(keypoints)
        keywords = jieba.analyse.extract_tags(text, topK=10)
        
        return {
            'word_count': word_count,
            'keypoint_count': keypoint_count,
            'top_keywords': keywords
        }
    
    def _generate_highlights(self, text, keypoints):
        """生成高亮标注元数据"""
        highlights = []
        for kp in keypoints:
            content = kp['content']
            start_pos = text.find(content)
            if start_pos != -1:
                highlights.append({
                    'id': kp['id'],
                    'start': start_pos,
                    'end': start_pos + len(content),
                    'text': content,
                    'color': kp['color'],
                    'importance': kp['importance'],
                    'annotation': kp['annotation'],
                    'category': kp['category']
                })
        return highlights

    def annotate_docx(self, input_path, highlights, output_path):
        """
        利用 Word 的 XML 结构进行物理标注
        """
        try:
            doc = Document(input_path)
            
            # 颜色映射 - 统一核心论点红色，论据蓝绿色
            color_map = {
                '#ff6b6b': WD_COLOR_INDEX.RED,         # 核心论点 - 统一红色
                '#51cf66': WD_COLOR_INDEX.BRIGHT_GREEN,# 支撑论据 - 统一亮绿色
                '#ffa94d': WD_COLOR_INDEX.DARK_YELLOW, # 兼容旧数据
                '#ffd43b': WD_COLOR_INDEX.YELLOW,      # 兼容旧数据
                '#74c0fc': WD_COLOR_INDEX.TURQUOISE    # 兼容旧数据
            }

            for hl in highlights:
                text_to_find = hl['text'].strip()
                if not text_to_find: continue
                
                # 遍历段落搜索
                for paragraph in doc.paragraphs:
                    if text_to_find in paragraph.text:
                        # 简单的替换式高亮（注意：这会破坏原文复杂的格式，但在分析预览中很有效）
                        # 对于精细标注，我们需要在 XML 层级分割 Run，这里采用稳健的全局标记法
                        # 将匹配到的文本拆分并重新设置 Run
                        if text_to_find in paragraph.text:
                            # 确定颜色
                            docx_color = color_map.get(hl['color'], WD_COLOR_INDEX.YELLOW)
                            
                            # 逻辑：将段落内容按匹配项拆分，重新构建 Runs
                            # 这种方法能确保 XML 结构中正确插入 <w:highlight>
                            orig_text = paragraph.text
                            parts = orig_text.split(text_to_find)
                            
                            paragraph.clear() # 清空旧 Runs
                            for i, part in enumerate(parts):
                                if part: paragraph.add_run(part)
                                if i < len(parts) - 1:
                                    run = paragraph.add_run(text_to_find)
                                    run.font.highlight_color = docx_color
            
            doc.save(output_path)
            return True
        except Exception as e:
            print(f"Docx 标注失败: {str(e)}")
            return False

    def annotate_pdf(self, input_path, highlights, output_path):
        """
        使用 pdfplumber + reportlab + PyMuPDF 的三层架构进行精确 PDF 标注
    
        流程：
          1. pdfplumber — 字符级搜索，获得每行精确 bbox（支持多行文本）
          2. reportlab — 创建全透明高亮覆盖层（半透明彩色框 + 左侧分类竖线）
          3. PyMuPDF  — 将覆盖层叠加到原始 PDF
    
        返回: [{'id': hl_id, 'page': page_num}, ...]
        """
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.colors import Color
    
        try:
            # ── Step 1: pdfplumber 字符级定位 ──────────────────────────
            print("📍 pdfplumber 字符级定位文本坐标...")
            location_map = {}  # {hl_id: [{'x0','top','x1','bottom','page_idx','page_w','page_h'}, ...]}
    
            with pdfplumber.open(input_path) as pdf:
                n_pages   = len(pdf.pages)
                page_sizes = [(p.width, p.height) for p in pdf.pages]
    
                for hl in highlights:
                    text   = hl['text'].strip()
                    hl_id  = hl['id']
                    page_hint = hl.get('page')  # 1-indexed 页码提示
    
                    if not text:
                        location_map[hl_id] = []
                        continue
    
                    # 确定搜索页面范围（优先在提示页附近搜索）
                    if page_hint and 1 <= page_hint <= n_pages:
                        seen = {}
                        for pg in [page_hint - 1,
                                   page_hint - 2 if page_hint > 1 else None,
                                   page_hint if page_hint < n_pages else None]:
                            if pg is not None and pg not in seen:
                                seen[pg] = True
                        search_range = list(seen.keys())
                    else:
                        search_range = list(range(n_pages))
    
                    found_locs = []
                    for page_idx in search_range:
                        bboxes = self._find_text_in_page(pdf.pages[page_idx], text)
                        if bboxes:
                            pw, ph = page_sizes[page_idx]
                            for bbox in bboxes:
                                bbox.update({'page_idx': page_idx,
                                             'page_w': pw, 'page_h': ph})
                            found_locs.extend(bboxes)
                            print(f"  \u2705 \u7b2c{page_idx + 1}\u9875: {text[:30]}...")
                            break  # \u627e\u5230\u5373\u505c
    
                    if not found_locs:
                        print(f"  ⚠️ 未定位: {text[:30]}...")
                    location_map[hl_id] = found_locs
    
            # ── Step 2: reportlab 创建高亮覆盖层 ──────────────────────
            print("🎨 reportlab 创建高亮覆盖层...")
            hl_map = {hl['id']: hl for hl in highlights}
    
            overlay_buf = io.BytesIO()
            c = rl_canvas.Canvas(overlay_buf)
    
            for page_idx, (pw, ph) in enumerate(page_sizes):
                c.setPageSize((pw, ph))
    
                for hl_id, locs in location_map.items():
                    page_locs = [l for l in locs if l.get('page_idx') == page_idx]
                    if not page_locs:
                        continue
    
                    hl = hl_map.get(hl_id)
                    if not hl:
                        continue
    
                    # 解析颜色
                    hex_col = hl['color'].lstrip('#')
                    rc = int(hex_col[0:2], 16) / 255.0
                    gc = int(hex_col[2:4], 16) / 255.0
                    bc = int(hex_col[4:6], 16) / 255.0
    
                    fill_col   = Color(rc, gc, bc, alpha=0.22)   # 半透明填充
                    border_col = Color(rc, gc, bc, alpha=0.60)   # 边框
                    bar_col    = Color(rc, gc, bc, alpha=0.92)   # 左侧竖线
    
                    for loc in page_locs:
                        # 坐标转换：
                        #   pdfplumber: 左上角原点, top = 距页面顶部的距离 (y 向下增)
                        #   reportlab : 左下角原点, y 向上增
                        x0 = loc['x0']
                        y0 = ph - loc['bottom']   # reportlab 中 bbox 的底边 y
                        w  = loc['x1'] - loc['x0']
                        h  = loc['bottom'] - loc['top']
    
                        # 半透明高亮矩形
                        c.setFillColor(fill_col)
                        c.setStrokeColor(border_col)
                        c.setLineWidth(0.4)
                        c.rect(x0, y0, w, h, fill=1, stroke=1)
    
                        # 左侧分类竖线标记
                        bar_x = max(3.0, x0 - 4.5)
                        c.setStrokeColor(bar_col)
                        c.setLineWidth(2.8)
                        c.line(bar_x, y0, bar_x, y0 + h)
    
                c.showPage()
    
            c.save()
            overlay_buf.seek(0)
    
            # ── Step 3: PyMuPDF 叠加到原始 PDF ───────────────────────
            print("🔗 PyMuPDF 叠加覆盖层...")
            original = fitz.open(input_path)
            overlay  = fitz.open("pdf", overlay_buf.read())
    
            for pg_num in range(len(original)):
                if pg_num < len(overlay):
                    original[pg_num].show_pdf_page(
                        original[pg_num].rect, overlay, pg_num
                    )
    
            original.save(output_path, garbage=4, deflate=True)
            original.close()
            overlay.close()
    
            # 构建 meta_map（返回每个高亮的实际页码）
            meta_map = []
            for hl in highlights:
                locs     = location_map.get(hl['id'], [])
                page_num = (locs[0]['page_idx'] + 1) if locs else (hl.get('page') or 1)
                meta_map.append({'id': hl['id'], 'page': page_num})
    
            located = sum(1 for locs in location_map.values() if locs)
            print(f"✅ 标注完成：{located}/{len(highlights)} 处成功定位")
            return meta_map
    
        except Exception as e:
            print(f"PDF 标注失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _find_text_in_page(self, page, target_text):
        """
        使用 pdfplumber 字符级定位文本，支持多行。
    
        算法：
          1. 提取页面所有非空白字符，拼接成无空格字符串
          2. 将目标文本同样去空格，用前 50 个字符定位起始位置
          3. 按 top 坐标近似分行，每行生成一个 bbox
    
        返回: [{'x0', 'top', 'x1', 'bottom'}, ...] 或 []
        """
        chars = page.chars
        if not chars:
            return []
    
        # 过滤空白字符
        non_blank = [c for c in chars if c['text'].strip()]
        if not non_blank:
            return []
    
        char_str     = ''.join(c['text'] for c in non_blank)
        target_clean = re.sub(r'\s+', '', target_text)
    
        # 用前 50 字符定位（太短则只用前 20 个）
        prefix_len = min(len(target_clean), 50)
        prefix = target_clean[:prefix_len].lower()
        idx = char_str.lower().find(prefix)
    
        if idx == -1 and prefix_len > 20:
            prefix = target_clean[:20].lower()
            idx = char_str.lower().find(prefix)
    
        if idx == -1:
            return []
    
        # 匹配字符范围
        end_idx      = min(idx + len(target_clean), len(non_blank))
        matched_chars = non_blank[idx:end_idx]
        if not matched_chars:
            return []
    
        # 按行分组（top 差异 < 4pt 视为同一行）
        LINE_TOL = 4
        lines, cur = [], [matched_chars[0]]
        for ch in matched_chars[1:]:
            if abs(ch['top'] - cur[-1]['top']) > LINE_TOL:
                lines.append(cur)
                cur = [ch]
            else:
                cur.append(ch)
        lines.append(cur)
    
        # 每行生成一个 bbox（加小量 padding 使高亮更自然）
        bboxes = []
        for line_chars in lines:
            bboxes.append({
                'x0':    min(c['x0']     for c in line_chars) - 0.5,
                'top':   min(c['top']    for c in line_chars) - 0.5,
                'x1':    max(c['x1']     for c in line_chars) + 0.5,
                'bottom':max(c['bottom'] for c in line_chars) + 0.5,
            })
        return bboxes
    
    
    def compare_documents(self, records):
        """比较多个文档"""
        comparison = {
            'common_keywords': [],
            'unique_keywords': {},
            'similarity': {}
        }
        
        # 提取每个文档的关键词
        all_keywords = {}
        for record in records:
            if record and 'analysis_result' in record:
                keywords = record['analysis_result']['statistics']['top_keywords']
                all_keywords[record['id']] = set(keywords)
        
        # 找出共同关键词
        if len(all_keywords) >= 2:
            common = set.intersection(*all_keywords.values())
            comparison['common_keywords'] = list(common)
            
            # 找出每个文档的独特关键词
            for record_id, keywords in all_keywords.items():
                unique = keywords - set(comparison['common_keywords'])
                comparison['unique_keywords'][record_id] = list(unique)
        
        return comparison
    
    def _locate_text_in_pdf(self, pdf_path, text, page_hint=None):
        """
        在PDF中精准定位文本位置
        结合多种方法：
        1. 如果有页码提示，优先在指定页查找
        2. 全文搜索匹配
        3. 模糊匹配
        返回: (page_num, bbox) 或 None
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_to_search = []
                
                # 决定搜索范围
                if page_hint and 1 <= page_hint <= len(pdf.pages):
                    # 优先搜索提示页，然后搜索相邻页
                    pages_to_search.append(page_hint - 1)  # 转为0索引
                    if page_hint > 1:
                        pages_to_search.append(page_hint - 2)
                    if page_hint < len(pdf.pages):
                        pages_to_search.append(page_hint)
                else:
                    # 搜索所有页
                    pages_to_search = list(range(len(pdf.pages)))
                
                # 在每一页中搜索
                for page_idx in pages_to_search:
                    page = pdf.pages[page_idx]
                    page_text = page.extract_text()
                    
                    # 精确匹配
                    if text in page_text:
                        print(f"✅ 在第 {page_idx + 1} 页找到文本: {text[:30]}...")
                        # 尝试获取详细位置（bbox）
                        words = page.extract_words()
                        for word in words:
                            if text.startswith(word['text']):
                                return (page_idx + 1, word)
                        return (page_idx + 1, None)
                    
                    # 模糊匹配（去除空白后匹配）
                    text_cleaned = ''.join(text.split())
                    page_cleaned = ''.join(page_text.split())
                    if text_cleaned in page_cleaned:
                        print(f"✅ 在第 {page_idx + 1} 页模糊匹配: {text[:30]}...")
                        return (page_idx + 1, None)
                
                print(f"⚠️ 未在PDF中找到文本: {text[:30]}...")
                return None
                
        except Exception as e:
            print(f"⚠️ PDF定位错误: {str(e)}")
            return None
