import fitz  # PyMuPDF - 用于提取图片和元数据
import pdfplumber  # 用于提取表格和精准文本位置

class EnhancedPDFParser:
    """
    增强版 PDF 解析器
    功能：
    1. 提取文本（保留页面和位置信息）
    2. 提取图片（生成描述符）
    3. 提取表格（结构化数据）
    4. 保留文档结构元数据（用于精准标注）
    """
    
    def __init__(self):
        self.structure_data = {}  # 存储文档结构元数据
    
    def parse_pdf_enhanced(self, filepath):
        """
        深度解析 PDF，提取多模态内容
        返回：
        {
            'text': str,  # 完整文本
            'structured_content': list,  # 结构化内容（包含页码、类型、位置）
            'metadata': dict  # 文档元数据
        }
        """
        result = {
            'text': '',
            'structured_content': [],
            'metadata': {}
        }
        
        try:
            # 使用 PyMuPDF 提取基础信息和图片
            fitz_doc = fitz.open(filepath)
            result['metadata'] = {
                'page_count': len(fitz_doc),
                'title': fitz_doc.metadata.get('title', ''),
                'author': fitz_doc.metadata.get('author', '')
            }
            
            # 使用 pdfplumber 提取文本和表格
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    print(f"正在解析第 {page_num}/{len(pdf.pages)} 页...")
                    
                    # 1. 提取文本块（保留位置信息）
                    text_blocks = self._extract_text_blocks(page, page_num)
                    result['structured_content'].extend(text_blocks)
                    
                    # 2. 提取表格
                    tables = self._extract_tables(page, page_num)
                    result['structured_content'].extend(tables)
                    
                    # 3. 提取图片描述
                    images = self._extract_images(fitz_doc[page_num - 1], page_num)
                    result['structured_content'].extend(images)
            
            # 生成完整文本（用于大模型分析）
            result['text'] = self._build_full_text(result['structured_content'])
            
            # 存储结构数据（用于后续精准标注）
            self.structure_data[filepath] = result['structured_content']
            
            fitz_doc.close()
            return result
            
        except Exception as e:
            print(f"PDF 深度解析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_text_blocks(self, page, page_num):
        """提取文本块并保留位置信息"""
        blocks = []
        
        # 使用 pdfplumber 的字符级提取
        words = page.extract_words(x_tolerance=3, y_tolerance=3)
        
        if not words:
            return blocks
        
        # 按行分组（根据 y 坐标）
        lines = {}
        for word in words:
            y = round(word['top'], 1)
            if y not in lines:
                lines[y] = []
            lines[y].append(word)
        
        # 构建文本块
        for y in sorted(lines.keys()):
            line_words = sorted(lines[y], key=lambda w: w['x0'])
            line_text = ' '.join([w['text'] for w in line_words])
            
            if line_text.strip():
                blocks.append({
                    'type': 'text',
                    'content': line_text.strip(),
                    'page': page_num,
                    'bbox': {
                        'x0': min([w['x0'] for w in line_words]),
                        'y0': min([w['top'] for w in line_words]),
                        'x1': max([w['x1'] for w in line_words]),
                        'y1': max([w['bottom'] for w in line_words])
                    }
                })
        
        return blocks
    
    def _extract_tables(self, page, page_num):
        """提取表格并转换为文本描述"""
        tables = []
        extracted_tables = page.extract_tables()
        
        for idx, table in enumerate(extracted_tables):
            if not table or len(table) == 0:
                continue
            
            # 转换表格为文本描述
            table_text = f"\n【表格 {idx + 1}】\n"
            
            # 处理表头
            if len(table) > 0 and table[0]:
                headers = [str(cell).strip() if cell else '' for cell in table[0]]
                table_text += " | ".join(headers) + "\n"
                table_text += "-" * 50 + "\n"
            
            # 处理数据行
            for row in table[1:]:
                if row:
                    row_data = [str(cell).strip() if cell else '' for cell in row]
                    table_text += " | ".join(row_data) + "\n"
            
            table_text += "\n"
            
            tables.append({
                'type': 'table',
                'content': table_text,
                'page': page_num,
                'table_data': table,  # 保留原始表格数据
                'bbox': page.bbox  # 表格大致位置
            })
        
        return tables
    
    def _extract_images(self, fitz_page, page_num):
        """提取图片并生成描述"""
        images = []
        image_list = fitz_page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            
            try:
                base_image = fitz_page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                
                # 获取图片信息
                img_ext = base_image["ext"]
                img_width = base_image.get("width", 0)
                img_height = base_image.get("height", 0)
                
                # 生成图片描述（简单版本）
                img_desc = f"\n【图片 {img_index + 1}】\n"
                img_desc += f"- 格式: {img_ext.upper()}\n"
                img_desc += f"- 尺寸: {img_width} x {img_height}\n"
                img_desc += "- 位置: 此处包含图片内容\n\n"
                
                images.append({
                    'type': 'image',
                    'content': img_desc,
                    'page': page_num,
                    'image_index': img_index,
                    'metadata': {
                        'format': img_ext,
                        'width': img_width,
                        'height': img_height
                    }
                })
                
            except Exception as e:
                print(f"图片提取失败 (xref={xref}): {str(e)}")
                continue
        
        return images
    
    def _build_full_text(self, structured_content):
        """从结构化内容构建完整文本（用于大模型分析）"""
        text_parts = []
        current_page = 0
        
        for item in structured_content:
            page = item.get('page', 0)
            
            # 添加页面分隔符
            if page != current_page:
                text_parts.append(f"\n\n===== 第 {page} 页 =====\n\n")
                current_page = page
            
            text_parts.append(item['content'])
        
        return ''.join(text_parts)
    
    def find_text_location(self, filepath, text_to_find):
        """
        在 PDF 中精确定位文本的页码和位置
        返回：{'page': int, 'bbox': dict} 或 None
        """
        if filepath not in self.structure_data:
            return None
        
        text_to_find_clean = text_to_find.strip()
        
        # 在结构化数据中搜索
        for item in self.structure_data[filepath]:
            if item['type'] == 'text' and text_to_find_clean in item['content']:
                return {
                    'page': item['page'],
                    'bbox': item.get('bbox', None),
                    'full_content': item['content']
                }
        
        # 模糊匹配（关键词重叠）
        best_match = None
        best_score = 0
        
        keywords = set(text_to_find_clean.split())
        
        for item in self.structure_data[filepath]:
            if item['type'] == 'text':
                item_keywords = set(item['content'].split())
                overlap = len(keywords & item_keywords)
                
                if overlap > best_score:
                    best_score = overlap
                    best_match = {
                        'page': item['page'],
                        'bbox': item.get('bbox', None),
                        'full_content': item['content']
                    }
        
        return best_match if best_score > 0 else None
