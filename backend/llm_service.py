import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 加载 .env 文件（位于当前脚本同目录）
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))


class LLMService:
    """大模型服务，支持 DeepSeek 和 Qwen 多种 API 提供商"""

    # API 提供商配置（密钥从环境变量读取，不硬编码）
    PROVIDER_CONFIGS = {
        'deepseek': {
            'api_url': 'https://api.deepseek.com/chat/completions',
            'model': 'deepseek-reasoner',
            'api_key': os.environ.get('DEEPSEEK_API_KEY', ''),
            'timeout': 120,
            'supports_json_format': False,   # deepseek-reasoner 不支持 json_object
            'display_name': 'DeepSeek-R1',
        },
        'qwen': {
            'api_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
            'model': 'qwen3.5-plus',
            'api_key': os.environ.get('QWEN_API_KEY', ''),
            'timeout': 60,
            'supports_json_format': False,
            'display_name': 'Qwen3.5-Plus',
        }
    }

    # 对话功能固定使用 DeepSeek-R1
    CHAT_CONFIG = {
        'api_url': 'https://api.deepseek.com/chat/completions',
        'model': 'deepseek-reasoner',
        'api_key': os.environ.get('DEEPSEEK_API_KEY', ''),
        'timeout': 120,
    }

    def __init__(self):
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY', '')
        qwen_key = os.environ.get('QWEN_API_KEY', '')
        if not deepseek_key:
            print('[WARN] DEEPSEEK_API_KEY 未配置，请在 backend/.env 中设置')
        if not qwen_key:
            print('[WARN] QWEN_API_KEY 未配置，请在 backend/.env 中设置')
        print('LLM 服务初始化，支持 DeepSeek-R1 和 Qwen3.5-Plus')

    def is_enabled(self) -> bool:
        return True

    def get_config_info(self) -> Dict:
        return {
            'providers': list(self.PROVIDER_CONFIGS.keys()),
            'chat_model': self.CHAT_CONFIG['model']
        }

    def _build_system_prompt(self, provider: str) -> str:
        """根据提供商构建系统提示词"""
        model_ref = self.PROVIDER_CONFIGS.get(provider, {}).get('display_name', 'DeepSeek-R1')

        intro = f'你是一个顶尖的文献情报专家，专门负责从海量信息中提取"干货"。请使用你的推理能力（{model_ref}）对文章进行穿透式分析：\n\n'

        body = '''### 核心任务：
1. **反直觉提取**：忽略那些显而易见的常识或背景介绍。专注于文章的"独特主张"、"突发结论"或"关键转折点"。
2. **智能调整数量**：根据文档长度和信息密度，自动调整论点数量（1-5个）。
3. **三位一体验证**：每个核心论点（Point）必须具备强力的支撑数据或逻辑推论（Evidence）。
4. **零公差引用（最关键）**：禁止对原文做任何润色、缩减或改写。`point` 和 `evidence.text` 必须是原文中连续、完整的字符串片段，**逐字精确复制**，包括标点、数字、空格。这是PDF物理标注的核心依据——字符完全一致才能在原文中精准定位。
5. **结构化内容理解**：如果文档包含表格、图片，请重点分析其中的数据规律和关键信息。
6. **精准位置标记（关键）**：对于PDF文档，必须精确记录每个 point 和 evidence 所在的页码（从1开始）；并提供 15-30 字的上下文片段（该文本前后的原文句子），用于在相同短语出现多次时进行精确区分定位。

### 分析流程：
- **Step 1 (Thought)**: 快速扫描文章，识别出哪些是填充物，哪些是金句。
- **Step 2 (Adaptive)**: 根据文档长度决定提取多少个论点（短文1-2个，中等长度3个，长文4-5个）。
- **Step 3 (Ranking)**: 将所有潜在论点按"信息密度"排序。
- **Step 4 (Scoring)**: 为每个论点分配 0-100 的重要性评分。
- **Step 5 (Locating)**: 如果是PDF，精确记录每个文本片段的页码和上下文片段。
- **Step 6 (Labeling)**: 为每个论点提炼一个 4-6 字的中文标注标签（annotation_label），概括该论点的核心主题，将显示在PDF边注中。

### 输出协议（JSON）:
{
  "core_arguments": [
    {
      "point": "必须是原文中的金句/核心主张（逐字精确复制，一字不差）",
      "point_page": 3,
      "point_context": "包含 point 的完整原句（用于定位消歧，精确复制15-30字）",
      "annotation_label": "核心结论",
      "evidence": [
        {
          "text": "支持该主张的原文证据句子（逐字精确复制，一字不差）",
          "page": 5,
          "context": "包含此 evidence 的完整原句（用于定位消歧，精确复制15-30字）"
        }
      ],
      "importance": 95,
      "rationale": "简要说明为何打 95 分"
    }
  ],
  "summary": "一句话概括全文",
  "title": "最能反映文章主旨的专业标题"
}

### 字段说明：
- **point / evidence.text**: 原文逐字复制，不得修改任何字符，这是PDF标注引擎搜索匹配的依据
- **point_page / page**: 文本所在页码（从1开始），缩小pdfplumber搜索范围，显著提升定位效率
- **point_context / evidence.context**: 包含目标文本的完整句子（原文复制），当同一短语在同页出现多次时用于精确区分
- **annotation_label**: 4-6字中文标签，将显示在PDF标注边注中，例如："核心结论"、"实验数据"、"方法论断"、"关键转折"
- **可选性**: 非PDF文档可省略页码和context字段

### 评分准则：
- **95-100 分**：文章的核心创新观点、颠覆性结论、独家数据
- **80-94 分**：强有力的支撑论证、关键转折点
- **60-79 分**：辅助性逻辑推导、背景性说明
- **低于 60 分**：均不应列入，需被过滤'''

        return intro + body

    def analyze_text(self, text: str, provider: str = 'deepseek',
                     pdf_path: Optional[str] = None, file_size: int = 0) -> Optional[Dict]:
        """
        使用指定 API 提供商分析文本
        Args:
            text: 文本内容
            provider: API 提供商 ('deepseek' | 'qwen')
            pdf_path: PDF 文件路径（用于格式化上传）
            file_size: 文件大小（字节，保留参数）
        """
        config = self.PROVIDER_CONFIGS.get(provider, self.PROVIDER_CONFIGS['deepseek'])
        system_prompt = self._build_system_prompt(provider)

        try:
            # 使用 DeepSeek 官方推荐的文件格式
            if pdf_path and pdf_path.lower().endswith('.pdf'):
                file_name = os.path.basename(pdf_path)
                formatted_content = f"""[file name]: {file_name}
[file content begin]
{text}
[file content end]
请对这份PDF文档进行穿透式分析，提取核心论点和证据，并记录页码信息。"""
                print(f"📄 使用 {config['display_name']} ({config['model']}) 处理PDF: {file_name}")
            else:
                formatted_content = text
                print(f"📝 使用 {config['display_name']} ({config['model']}) 分析文本")

            response = self._call_api(formatted_content, system_prompt, config)

            if response:
                return self._parse_llm_response(response)
            return None
        except Exception as e:
            print(f"分析错误 ({provider}): {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def chat(self, message: str, document_context: str, chat_history: List[Dict]) -> Optional[str]:
        """
        AI 对话（固定使用 DeepSeek-R1）
        Args:
            message: 用户消息
            document_context: 当前文档上下文
            chat_history: 对话历史 [{'role': 'user'|'assistant', 'content': str}]
        """
        config = self.CHAT_CONFIG

        if document_context:
            system_prompt = f"""你是一个专业的文档分析助手（由 DeepSeek-R1 驱动），正在帮助用户深入理解和分析当前文档。

当前文档内容：
---
{document_context[:3000]}
---

请基于以上文档内容回答用户问题，分析要有洞察力和深度。
- 如果问题在文档中有答案，直接引用原文并给出分析
- 如果超出文档范围，正常回答但说明该内容不在文档中
- 语言简洁清晰，使用中文回答"""
        else:
            system_prompt = "你是一个专业的文档分析助手（由 DeepSeek-R1 驱动），请帮助用户分析和理解文档内容。使用中文回答。"

        messages = [{'role': 'system', 'content': system_prompt}]

        # 添加对话历史（最多 10 条）
        for msg in chat_history[-10:]:
            messages.append({'role': msg['role'], 'content': msg['content']})

        messages.append({'role': 'user', 'content': message})

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config["api_key"]}'
        }
        data = {
            'model': config['model'],
            'messages': messages,
            'temperature': 0.7
        }

        try:
            response = requests.post(
                config['api_url'],
                headers=headers,
                json=data,
                timeout=config['timeout']
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"Chat API 错误: {response.status_code}, {response.text}")
                return None
        except requests.exceptions.Timeout:
            print("Chat 请求超时")
            return None
        except Exception as e:
            print(f"Chat 错误: {str(e)}")
            return None

    def _call_api(self, user_content: str, system_prompt: str, config: dict) -> Optional[str]:
        """调用指定配置的 API"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config["api_key"]}'
        }
        data = {
            'model': config['model'],
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"请对以下文章进行穿透式分析：\n\n{user_content[:12000]}"}
            ],
            'temperature': 1.0
        }

        if config.get('supports_json_format'):
            data['response_format'] = {'type': 'json_object'}

        try:
            response = requests.post(
                config['api_url'],
                headers=headers,
                json=data,
                timeout=config.get('timeout', 60)
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"API 错误: 状态码={response.status_code}, 响应={response.text}")
                return None
        except requests.exceptions.Timeout:
            print(f"请求超时 ({config.get('timeout', 60)}s)：大模型响应过慢，请稍后重试。")
            return None
        except Exception as e:
            print(f"请求异常: {str(e)}")
            return None

    def _parse_llm_response(self, response: str) -> Optional[Dict]:
        """解析大模型返回的 JSON 结果"""
        try:
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]

            if response.endswith('```'):
                response = response[:-3]

            response = response.strip()
            result = json.loads(response)

            if 'core_arguments' in result and isinstance(result['core_arguments'], list):
                return result

            # 兼容旧版本结构
            if 'keypoints' in result and isinstance(result['keypoints'], list):
                result['core_arguments'] = [
                    {'point': kp.get('content', ''), 'evidence': kp.get('keywords', [])}
                    for kp in result['keypoints']
                ]
                return result

            print(f"JSON 结果结构不符合预期。字段: {list(result.keys())}")
            print(f"内容详情: {response[:500]}...")
            return None

        except json.JSONDecodeError as e:
            print(f"解析大模型返回结果失败: {str(e)}")
            print(f"原始响应内容: {response}")
            return None
