import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 加载 .env 文件（位于当前脚本同目录）
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))


class LLMService:
    """
    大模型服务 — 全配置从环境变量读取，后端零硬编码

    新增 provider 只需：
      ① 在 PROVIDERS 列表添加名称（如 'openai'）
      ② 在 backend/.env 添加 OPENAI_API_KEY / _API_URL / _MODEL / _TIMEOUT / _DISPLAY_NAME
    """

    # ── 已注册的 provider 名称列表（所有配置从 .env 读取）──
    PROVIDERS = ['deepseek', 'qwen']

    def __init__(self):
        self.chat_provider = os.environ.get('CHAT_PROVIDER', 'deepseek')
        available = []
        for name in self.PROVIDERS:
            cfg = self._get_provider_config(name)
            if cfg['api_key']:
                available.append(cfg['display_name'])
            else:
                prefix = name.upper()
                print(f'[WARN] {prefix}_API_KEY 未配置，请在 backend/.env 中设置')

        status = '、'.join(available) if available else '无可用 provider'
        print(f'LLM 服务初始化，可用: {status}')

    def _get_provider_config(self, provider: str) -> dict:
        """获取指定 provider 的完整配置（全部从环境变量读取，零硬编码）"""
        prefix = provider.upper()
        return {
            'provider': provider,
            'api_key': os.environ.get(f'{prefix}_API_KEY', ''),
            'api_url': os.environ.get(f'{prefix}_API_URL', ''),
            'model': os.environ.get(f'{prefix}_MODEL', ''),
            'file_model': os.environ.get(f'{prefix}_FILE_MODEL', ''),
            'timeout': int(os.environ.get(f'{prefix}_TIMEOUT', '60')),
            'display_name': os.environ.get(f'{prefix}_DISPLAY_NAME', provider),
            'supports_json_format': os.environ.get(f'{prefix}_SUPPORTS_JSON', '').lower() == 'true',
        }

    def is_enabled(self) -> bool:
        return True

    def get_config_info(self) -> Dict:
        return {
            'providers': list(self.PROVIDERS),
            'chat_provider': self.chat_provider
        }

    def _build_system_prompt(self, provider: str) -> str:
        """根据提供商构建系统提示词"""
        config = self._get_provider_config(provider)

        model_ref = config.get('display_name', 'DeepSeek-R1')

        prompt = f'''你是一个顶尖的文献情报分析专家（{model_ref}），专精于从学术论文、技术文档和深度报道中提取核心洞见。

<task>
对提供的文档进行深度分析，提取 2-8 个核心论点及其支撑论据。
论点数量根据文档长度和信息密度动态调整：
- 短文（<2000字）：2-3 个
- 中等（2000-8000字）：3-5 个
- 长文（>8000字）：5-8 个
</task>

<rules>
1. **逐字引用原则**（最关键）：
   - point 和 evidence.text 必须从原文中**逐字精确复制**，包含完整的句子（从句首到句末标点）
   - 绝对禁止截断半句话、绝对禁止改写润色替换任何字词
   - 宁长勿短——如果论点跨越多句，完整复制所有相关句子
   - 这是 PDF 物理标注的依据，字符不一致 = 标注失败

2. **筛选标准**：
   - 忽略常识性背景介绍和填充性内容
   - 专注于：独特主张、关键数据、核心创新、方法突破、重要结论
   - 每个论点至少 2 条论据支撑

3. **精准定位**（PDF 文档必须）：
   - 记录每个 point 和 evidence 所在的页码（从1开始）
   - 提供 point_context：point 所在段落的前后文（15-30 字原文片段），用于同页多次出现时的精准定位

4. **标注标签**：
   - 为每个论点生成 annotation_label（4-6 字中文标签），如 "核心结论"、"实验数据"、"方法创新"
</rules>

<steps>
1. 通读全文，区分填充内容与核心洞见
2. 根据文档长度确定提取 2-8 个论点
3. 逐字复制完整原句作为 point（从句首到句末标点）
4. 为每个论点找到至少 2 条完整原句作为 evidence
5. 评分（0-100）并记录页码和上下文
</steps>

<output_format>
严格输出以下 JSON 结构（不要输出其他任何内容）：
{{
  "core_arguments": [
    {{
      "point": "原文完整句子（逐字复制，从句首到句末标点）",
      "point_page": 3,
      "point_context": "point 前后 15-30 字原文片段（用于定位消歧）",
      "annotation_label": "核心结论",
      "evidence": [
        {{
          "text": "论据原文完整句子（逐字复制）",
          "page": 5,
          "context": "evidence 前后 15-30 字原文片段"
        }}
      ],
      "importance": 95,
      "rationale": "评分理由"
    }}
  ],
  "key_data": [
    {{
      "label": "数据指标名称（如“准确率”、“F1-Score”、“市场规模”）",
      "value": "具体数值或百分比（如“94.5%”、“1.2万亿”）",
      "context": "数据的上下文说明（如“在MMLU基准测试中”）",
      "page": 5
    }}
  ],
  "summary": "一句话概括全文核心",
  "title": "反映文章主旨的标题"
}}
</output_format>

<key_data_rules>
提取文档中所有有意义的定量数据、指标、统计结果：
- 实验数据：准确率、召回率、F1-Score、BLEU、ROUGE 等
- 统计数据：百分比、增长率、规模、数量
- 对比数据：提升/降低幅度、before/after
- 如果文档无定量数据，key_data 返回空数组 []
</key_data_rules>

<scoring>
- 95-100：核心创新观点、颠覆性结论、独家数据
- 80-94：强支撑论证、关键转折点
- 60-79：辅助逻辑推导
- <60：过滤不列入
</scoring>'''

        return prompt

    def analyze_text(self, text: str, provider: str = 'deepseek',
                     file_path: Optional[str] = None, file_size: int = 0,
                     image_descriptions: str = '') -> Optional[Dict]:
        """
        使用指定 API 提供商分析文档

        优先策略：文件直传 API（上传文件 + prompt） → 降级为文本提取模式

        Args:
            text: 已提取的文本内容（用于降级 + 标注搜索）
            provider: API 提供商 ('deepseek' | 'qwen')
            file_path: 原始文件路径（PDF/Word/Markdown 等）
            file_size: 文件大小（字节）
            image_descriptions: 图片独立分析结果（两阶段第一阶段输出）
        """
        config = self._get_provider_config(provider)
        system_prompt = self._build_system_prompt(provider)

        try:
            # ── 优先方案：文件直传 API ──────────────────────────
            # 上传原始文件 → API 自行解析 → 返回分析结果
            if file_path and os.path.exists(file_path):
                file_id = self._upload_file(file_path, config)
                if file_id:
                    file_name = os.path.basename(file_path)
                    user_prompt = f"请对文档 {file_name} 进行穿透式分析，提取核心论点和证据，并精确记录页码信息。"
                    if image_descriptions:
                        user_prompt += f"\n\n【图片独立分析结果】\n{image_descriptions}"

                    # 使用文件专用模型（如 qwen-long）或默认模型
                    file_model = config.get('file_model') or config['model']
                    print(f"📤 文件直传模式：{config['display_name']}（{file_model}）分析 {file_name}")

                    response = self._call_api_with_file(file_id, system_prompt, user_prompt, config, file_model)

                    # 清理已上传的文件
                    self._delete_uploaded_file(file_id, config)

                    if response:
                        result = self._parse_llm_response(response)
                        if result:
                            return result
                    print("⚠️ 文件直传分析失败，降级为文本提取模式")

            # ── 降级方案：文本提取模式 ────────────────────────
            final_content = text

            if image_descriptions:
                final_content += f"\n\n{'='*50}\n【图片分析结果】\n以下是文档中图片经独立分析后得到的描述，请结合这些图片信息进行整体分析：\n{image_descriptions}\n{'='*50}"

            if file_path and file_path.lower().endswith('.pdf'):
                file_name = os.path.basename(file_path)
                formatted_content = f"""[file name]: {file_name}
[file content begin]
{final_content}
[file content end]
请对这份PDF文档进行穿透式分析，提取核心论点和证据，并记录页码信息。"""
                print(f"📄 文本提取模式：{config['display_name']}（{config['model']}）处理 {file_name}")
            else:
                formatted_content = final_content
                print(f"📝 文本提取模式：{config['display_name']}（{config['model']}）分析文本")

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
        AI 对话（使用 CHAT_PROVIDER 指定的 provider）
        Args:
            message: 用户消息
            document_context: 当前文档上下文
            chat_history: 对话历史 [{'role': 'user'|'assistant', 'content': str}]
        """
        config = self._get_provider_config(self.chat_provider)
        model_name = config['display_name']

        if document_context:
            system_prompt = f"""你是一个专业的文档分析助手（由 {model_name} 驱动），正在帮助用户深入理解和分析当前文档。

当前文档内容：
---
{document_context[:3000]}
---

请基于以上文档内容回答用户问题，分析要有洞察力和深度。
- 如果问题在文档中有答案，直接引用原文并给出分析
- 如果超出文档范围，正常回答但说明该内容不在文档中
- 语言简洁清晰，使用中文回答"""
        else:
            system_prompt = f"你是一个专业的文档分析助手（由 {model_name} 驱动），请帮助用户分析和理解文档内容。使用中文回答。"

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

    # ── 文件直传 API 方法 ─────────────────────────────────────

    def _get_base_url(self, config: dict) -> str:
        """从 chat/completions URL 推导出 API base URL"""
        api_url = config['api_url']
        # 移除 /chat/completions 得到 base URL
        for suffix in ['/chat/completions', '/chat']:
            if suffix in api_url:
                return api_url.split(suffix)[0]
        return api_url

    def _upload_file(self, filepath: str, config: dict) -> Optional[str]:
        """
        上传文件到 API 的 /files 端点（OpenAI 兼容格式）
        支持 DashScope、OpenAI 等提供文件上传接口的 API
        返回 file_id 或 None（表示该 provider 不支持文件上传）
        """
        base_url = self._get_base_url(config)
        files_url = f"{base_url}/files"

        try:
            file_name = os.path.basename(filepath)
            with open(filepath, 'rb') as f:
                response = requests.post(
                    files_url,
                    headers={'Authorization': f'Bearer {config["api_key"]}'},
                    files={'file': (file_name, f)},
                    data={'purpose': 'file-extract'},
                    timeout=120  # 上传可能较慢
                )

            if response.status_code == 200:
                result = response.json()
                file_id = result.get('id', '')
                if file_id:
                    print(f"  📤 文件上传成功: {file_id} ({file_name})")
                    return file_id
                print(f"  ⚠️ 文件上传返回无 id: {result}")
            else:
                # 404/405 = 该 provider 不支持文件上传，静默降级
                if response.status_code in (404, 405):
                    print(f"  ℹ️ {config['display_name']} 不支持文件上传接口，使用文本提取模式")
                else:
                    print(f"  ⚠️ 文件上传失败: {response.status_code} {response.text[:200]}")
        except requests.exceptions.ConnectionError:
            print(f"  ℹ️ 文件上传接口不可用，使用文本提取模式")
        except Exception as e:
            print(f"  ⚠️ 文件上传异常: {str(e)}")

        return None

    def _call_api_with_file(self, file_id: str, system_prompt: str,
                            user_prompt: str, config: dict, model: str) -> Optional[str]:
        """
        使用文件引用调用 API（fileid:// 格式，DashScope/OpenAI 兼容）
        文件内容由 API 端直接解析，无需本地文本提取
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config["api_key"]}'
        }
        data = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'system', 'content': f'fileid://{file_id}'},
                {'role': 'user', 'content': user_prompt}
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
                timeout=config.get('timeout', 120)
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"  文件分析 API 错误: {response.status_code}, {response.text[:300]}")
                return None
        except requests.exceptions.Timeout:
            print(f"  文件分析请求超时 ({config.get('timeout', 120)}s)")
            return None
        except Exception as e:
            print(f"  文件分析异常: {str(e)}")
            return None

    def _delete_uploaded_file(self, file_id: str, config: dict):
        """删除已上传的文件（清理 API 端存储）"""
        base_url = self._get_base_url(config)
        delete_url = f"{base_url}/files/{file_id}"

        try:
            response = requests.delete(
                delete_url,
                headers={'Authorization': f'Bearer {config["api_key"]}'},
                timeout=10
            )
            if response.status_code == 200:
                print(f"  🗑️ 已清理上传文件: {file_id}")
        except Exception:
            pass  # 清理失败不影响主流程

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

    def analyze_images(self, image_infos: list, provider: str = 'deepseek') -> str:
        """
        独立分析文档中的图片信息（两阶段处理的第一阶段）
        Args:
            image_infos: 图片信息列表 [{'page': int, 'content': str, 'metadata': dict}, ...]
            provider: API 提供商
        Returns:
            图片分析描述文本
        """
        if not image_infos:
            return ''

        config = self._get_provider_config(provider)

        # 构建图片分析提示
        image_prompt = "你是一个专业的文档图片分析专家。以下是从文档中提取的图片信息（包括格式、尺寸和在文档中的位置上下文）。\n"
        image_prompt += "请对每张图片进行分析，推断其可能的内容和作用，并说明其与文档主题的关系。\n\n"

        for idx, img in enumerate(image_infos):
            page = img.get('page', '未知')
            content = img.get('content', '')
            metadata = img.get('metadata', {})
            context = img.get('surrounding_text', '')

            image_prompt += f"--- 图片 {idx + 1}（第 {page} 页）---\n"
            image_prompt += f"格式: {metadata.get('format', '未知').upper()}, 尺寸: {metadata.get('width', 0)}x{metadata.get('height', 0)}\n"
            if context:
                image_prompt += f"图片周围的文本上下文:\n{context}\n"
            image_prompt += "\n"

        image_prompt += "请为每张图片提供：\n1. 推断的图片内容描述\n2. 图片在文档论证中的作用\n3. 关键数据或信息（如果可以推断）\n"
        image_prompt += "请用简洁的中文回答。"

        try:
            print(f"🖼️ 使用 {config['display_name']} 独立分析 {len(image_infos)} 张图片...")
            result = self._call_api(image_prompt, "你是专业的文档图片分析专家，擅长根据图片的元数据和上下文推断图片内容。", config)
            if result:
                print(f"✅ 图片分析完成")
                return result
            return ''
        except Exception as e:
            print(f"图片分析失败: {str(e)}")
            return ''
