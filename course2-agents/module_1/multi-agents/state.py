
# state.py
from typing import Dict, List

# 简单的内存存储（示例用，生产要换成 DB / 向量库）
MEMORY: Dict[str, str] = {}
CHORE_LOG: List[str] = []