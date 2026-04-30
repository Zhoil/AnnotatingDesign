"""
论证链路生成器：基于文档分析结果中已有的 keypoints 在本地构建
"论点 → 论据" 可视化链路，输出 Mermaid 源码与结构化 JSON。

- 零 LLM 额外调用：直接复用 TextAnalyzer 产出的 category / annotation_label / evidence 字段
- 输出 graph TD：中心节点=文档标题，一级=核心论点（按 importance 排序），二级=论据

节点 ID 规则：
  doc       文档根节点
  k{idx}    第 idx 个核心论点
  e{idx}_{j} 第 idx 个论点下的第 j 条论据
"""

import re
from typing import Dict, List


# Mermaid 对节点文本的特殊字符较敏感，统一做一次转义
_MERMAID_ESCAPE_RE = re.compile(r'["`\[\]{}()<>|]')


def _safe_text(text: str, max_len: int = 48) -> str:
    if not text:
        return ''
    s = str(text).replace('\n', ' ').replace('\r', ' ').strip()
    s = _MERMAID_ESCAPE_RE.sub(' ', s)
    s = re.sub(r'\s+', ' ', s)
    if len(s) > max_len:
        s = s[: max_len - 1] + '…'
    return s


def _filter_core_points(keypoints: List[Dict]) -> List[Dict]:
    """筛选核心论点（兼容缺少 category 字段的旧数据）。"""
    if not keypoints:
        return []
    cores = [kp for kp in keypoints if (kp.get('category') or '') == '核心论点']
    if cores:
        return cores
    # 退化策略：按 importance 排序后取 Top-N
    sorted_kp = sorted(keypoints, key=lambda x: int(x.get('importance', 0) or 0), reverse=True)
    return sorted_kp[: min(6, len(sorted_kp))]


def build_logic_tree(record: Dict, max_points: int = 6, max_evidence_per_point: int = 3) -> Dict:
    """
    根据数据库记录构建论证链路。
    返回：
        {
          'mermaid': '...graph TD...',
          'tree': { root, points: [{id, text, importance, evidences: [...]}] },
          'stats': { points, evidences }
        }
    """
    title = record.get('title') or record.get('filename') or '当前文档'
    keypoints = record.get('keypoints') or []
    cores = _filter_core_points(keypoints)
    cores = sorted(cores, key=lambda x: int(x.get('importance', 0) or 0), reverse=True)[:max_points]

    # ───── 构建 mermaid ─────
    lines = ['graph TD']
    root_id = 'DOC'
    lines.append(f'    {root_id}(["📄 {_safe_text(title, 36)}"])')

    tree_points = []
    total_ev = 0
    for i, kp in enumerate(cores, start=1):
        kp_id = f'K{i}'
        importance = int(kp.get('importance', 0) or 0)
        label_text = (kp.get('annotation_label') or '').strip() or f'论点 {i}'
        content = _safe_text(kp.get('content') or '', max_len=56)
        node_label = f'<b>{_safe_text(label_text, 16)}</b><br/>{content}<br/>⭐{importance}'
        # 用方括号 + 单引号防止内嵌字符冲突
        lines.append(f'    {kp_id}["{node_label}"]')
        lines.append(f'    {root_id} --> {kp_id}')

        # 论据子节点
        evidences = (kp.get('evidence') or [])[:max_evidence_per_point]
        ev_list = []
        for j, ev in enumerate(evidences, start=1):
            ev_id = f'E{i}_{j}'
            ev_text = _safe_text(ev.get('text') or '', max_len=48)
            page = ev.get('page')
            ev_label = ev_text + (f'<br/>📄p.{page}' if page else '')
            lines.append(f'    {ev_id}(["{ev_label}"])')
            lines.append(f'    {kp_id} -.-> {ev_id}')
            ev_list.append({
                'id': ev_id,
                'text': ev.get('text') or '',
                'page': page
            })
        total_ev += len(ev_list)

        # 节点配色按重要性
        if importance >= 80:
            cls = 'critical'
        elif importance >= 60:
            cls = 'high'
        elif importance >= 40:
            cls = 'medium'
        else:
            cls = 'low'
        lines.append(f'    class {kp_id} {cls};')

        tree_points.append({
            'id': kp_id,
            'text': kp.get('content') or '',
            'label': label_text,
            'importance': importance,
            'page': kp.get('page'),
            'evidences': ev_list
        })

    # 类样式（前端 mermaid 渲染时会读取）
    lines.append('    classDef critical fill:#ffe4e1,stroke:#ff6b6b,stroke-width:2px,color:#7a1f1f;')
    lines.append('    classDef high fill:#fff4e6,stroke:#ffa94d,stroke-width:2px,color:#7a4a1f;')
    lines.append('    classDef medium fill:#fff9e6,stroke:#ffd43b,stroke-width:1.5px,color:#7a6a1f;')
    lines.append('    classDef low fill:#e8f3ff,stroke:#74c0fc,stroke-width:1.5px,color:#1f4a7a;')
    lines.append(f'    style {root_id} fill:#3a9fd8,stroke:#2a7fb8,color:#ffffff,stroke-width:3px;')

    mermaid_src = '\n'.join(lines)

    return {
        'mermaid': mermaid_src,
        'tree': {
            'root': title,
            'points': tree_points
        },
        'stats': {
            'points': len(tree_points),
            'evidences': total_ev
        }
    }
