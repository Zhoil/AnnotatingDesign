import requests
from bs4 import BeautifulSoup
import re

class EnhancedWebParser:
    """
    增强版网页解析器
    功能：
    1. 保留网页HTML结构
    2. 提取主要内容区域
    3. 标注关键点位置
    4. 生成可标注的HTML
    """
    
    def __init__(self):
        self.original_html = None
        self.soup = None
        self.main_content_selector = None
    
    def parse_url(self, url):
        """
        解析网页URL，提取结构化内容
        返回: {
            'text': str,  # 纯文本（用于大模型分析）
            'html': str,  # 原始完整HTML（保留所有样式）
            'structured_content': list,  # 结构化内容
            'metadata': dict
        }
        """
        try:
            # 获取网页内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = response.apparent_encoding
            
            # 保存原始完整HTML
            self.original_html = response.text
            self.soup = BeautifulSoup(self.original_html, 'html.parser')
            
            # 提取元数据
            metadata = self._extract_metadata()
            
            # 只移除脚本，保留所有样式和HTML结构
            self._remove_noise()
            
            # 识别主要内容区域（用于提取文本）
            main_content = self._find_main_content()
            
            # 提取结构化内容（用于文本分析）
            structured_content = self._extract_structured_content(main_content)
            
            # 提取纯文本（用于大模型分析）
            text = self._extract_text(main_content)
            
            return {
                'text': text,
                'html': str(self.soup),  # 返回完整的HTML（包含所有样式）
                'original_html': self.original_html,
                'structured_content': structured_content,
                'metadata': metadata,
                'url': url
            }
            
        except Exception as e:
            print(f"网页解析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_metadata(self):
        """提取网页元数据"""
        title = self.soup.find('title')
        title_text = title.text.strip() if title else '未命名网页'
        
        # 尝试提取描述
        description_meta = self.soup.find('meta', attrs={'name': 'description'})
        description = description_meta.get('content', '') if description_meta else ''
        
        # 尝试提取作者
        author_meta = self.soup.find('meta', attrs={'name': 'author'})
        author = author_meta.get('content', '') if author_meta else ''
        
        return {
            'title': title_text,
            'description': description,
            'author': author
        }
    
    def _remove_noise(self):
        """移除干扰元素（但保留主体HTML结构和所有样式）"""
        # 只移除脚本，保留所有CSS样式
        for element in self.soup(['script']):
            element.decompose()
    
    def _find_main_content(self):
        """识别主要内容区域"""
        # 尝试常见的内容标签
        main_content = (
            self.soup.find('article') or
            self.soup.find('main') or
            self.soup.find('div', class_=re.compile(r'content|article|post|entry', re.I)) or
            self.soup.find('div', id=re.compile(r'content|article|post|main', re.I)) or
            self.soup.find('body')
        )
        
        return main_content
    
    def _extract_structured_content(self, content_element):
        """提取结构化内容（段落、标题等）"""
        structured_content = []
        
        if not content_element:
            return structured_content
        
        # 提取标题和段落
        for idx, element in enumerate(content_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])):
            text = element.get_text(strip=True)
            if not text or len(text) < 10:
                continue
            
            # 为每个元素添加唯一ID（用于后续标注）
            element_id = f"content-{idx}"
            element['data-content-id'] = element_id
            
            structured_content.append({
                'type': element.name,
                'content': text,
                'id': element_id,
                'html_tag': element.name
            })
        
        return structured_content
    
    def _extract_text(self, content_element):
        """提取纯文本内容"""
        if not content_element:
            return ""
        
        text = content_element.get_text(separator='\n', strip=True)
        # 清理多余空白
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def annotate_html(self, highlights):
        """
        在完整的HTML中标注关键点（保留原网页所有样式和结构）
        highlights: [{'text': str, 'color': str, 'id': int}]
        返回: 标注后的HTML字符串
        """
        if not self.soup:
            return None
        
        # 为每个高亮创建标注
        for hl in highlights:
            text_to_find = hl['text'].strip()
            if not text_to_find:
                continue
            
            # 在body中的所有文本节点中查找并替换
            self._highlight_text_in_soup(text_to_find, hl['color'], hl['id'])
        
        # 添加标注样式（使用!important确保优先级）
        style_tag = self.soup.new_tag('style')
        style_tag.string = """
        /* AI标注样式 - 确保在所有网页上都能正确显示 */
        .ai-highlight {
            background-color: var(--highlight-color) !important;
            border-bottom: 2px solid var(--highlight-border) !important;
            padding: 2px 4px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            position: relative !important;
            display: inline !important;
            border-radius: 3px !important;
            line-height: inherit !important;
            font-size: inherit !important;
            font-family: inherit !important;
            z-index: 1 !important;
        }
        .ai-highlight:hover {
            filter: brightness(0.85) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
            transform: translateY(-1px) !important;
        }
        .ai-highlight-point {
            font-weight: 600 !important;
            border-bottom-width: 3px !important;
            border-bottom-style: solid !important;
            background-color: rgba(255, 107, 107, 0.35) !important;
        }
        .ai-highlight-evidence {
            border-bottom-style: dotted !important;
            font-weight: 500 !important;
            background-color: rgba(81, 207, 193, 0.25) !important;
        }
        /* 确保标注不破坏页面布局 */
        .ai-highlight * {
            line-height: inherit !important;
        }
        """
        
        if self.soup.head:
            self.soup.head.append(style_tag)
        else:
            # 如果没有head，创建一个
            head = self.soup.new_tag('head')
            head.append(style_tag)
            if self.soup.html:
                self.soup.html.insert(0, head)
        
        return str(self.soup)
    
    def _highlight_text_in_soup(self, text_to_find, color, highlight_id):
        """在BeautifulSoup中高亮文本（智能查找，忽略空白差异）"""
        # 判断是论点还是论据
        is_point = color == '#ff6b6b'
        css_class = 'ai-highlight ai-highlight-point' if is_point else 'ai-highlight ai-highlight-evidence'
            
        # 清理文本：移除多余空白
        text_to_find_cleaned = ' '.join(text_to_find.split())
            
        # 遵历所有文本节点（优先在body中查找）
        body = self.soup.find('body')
        search_root = body if body else self.soup
            
        found = False
        for element in search_root.find_all(text=True):
            if element.parent.name in ['script', 'style', 'head', 'meta', 'link']:
                continue
                
            text = str(element)
            text_cleaned = ' '.join(text.split())
                
            # 精确匹配或模糊匹配
            if text_to_find in text or text_to_find_cleaned in text_cleaned:
                # 找到匹配的位置
                if text_to_find in text:
                    match_text = text_to_find
                    parts = text.split(text_to_find, 1)
                else:
                    # 模糊匹配：查找最接近的子串
                    import re
                    pattern = re.escape(text_to_find_cleaned).replace(r'\ ', r'\s+')
                    match = re.search(pattern, text)
                    if not match:
                        continue
                    match_text = match.group(0)
                    parts = [text[:match.start()], text[match.end():]]
                    
                # 创建新的内容
                new_content = []
                if parts[0]:
                    new_content.append(parts[0])
                    
                # 创建高亮标签
                mark_tag = self.soup.new_tag(
                    'mark',
                    attrs={
                        'class': css_class,
                        'data-highlight-id': highlight_id,
                        'style': f'--highlight-color: {color}55; --highlight-border: {color};'
                    }
                )
                mark_tag.string = match_text
                new_content.append(mark_tag)
                    
                if len(parts) > 1 and parts[1]:
                    new_content.append(parts[1])
                    
                # 替换原文本节点
                parent = element.parent
                element.replace_with(*new_content)
                found = True
                break  # 只替换第一次出现
            
        if not found:
            print(f"⚠️ 未找到文本: {text_to_find[:50]}...")
