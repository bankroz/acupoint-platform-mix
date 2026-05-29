"""
专家修正数据存储模块。
MVP 阶段使用 JSON 文件存储，后续可换 SQLite。
"""

import json
import os
import time
import uuid
from typing import Optional

from config import CORRECTIONS_DIR
from schemas.models import ExpertCorrection


def _get_corrections_file(patient_id: str) -> str:
    """获取某个患者的修正记录文件路径"""
    return os.path.join(CORRECTIONS_DIR, f"corrections_{patient_id}.json")


def save_correction(correction: ExpertCorrection) -> ExpertCorrection:
    """保存一条专家修正记录"""
    if not correction.correction_id:
        correction.correction_id = f"corr_{uuid.uuid4().hex[:8]}"
    if not correction.timestamp:
        correction.timestamp = time.time()

    filepath = _get_corrections_file(correction.patient_id)

    # 读取已有记录
    records: list[dict] = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            records = json.load(f)

    records.append(correction.model_dump())

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    return correction


def get_corrections(patient_id: str, acupoint_id: Optional[str] = None) -> list[ExpertCorrection]:
    """获取患者的修正记录，可按穴位筛选"""
    filepath = _get_corrections_file(patient_id)
    if not os.path.exists(filepath):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        records = json.load(f)

    corrections = [ExpertCorrection(**r) for r in records]

    if acupoint_id:
        corrections = [c for c in corrections if c.acupoint_id == acupoint_id]

    return corrections
