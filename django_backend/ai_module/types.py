from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Part:
    partId: str
    order: int
    title: str
    minutes: int
    notes: Optional[str] = None  # “要做什么”描述

@dataclass
class TaskWithParts:
    taskId: str
    taskTitle: str
    dueDate: str  # ISO yyyy-mm-dd
    parts: List[Part]

@dataclass
class Preferences:
    daily_hour_cap: int            # 每天学习小时数（整数小时）
    weekly_study_days: int         # 每周学习天数（1~7）
    avoid_days: Optional[list] = None   # 不学习日，0=Mon … 6=Sun