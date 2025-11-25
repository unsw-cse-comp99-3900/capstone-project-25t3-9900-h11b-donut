from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Part:
    partId: str
    order: int
    title: str
    minutes: int
    notes: Optional[str] = None  # what to do

@dataclass
class TaskWithParts:
    taskId: str
    taskTitle: str
    dueDate: str  # ISO yyyy-mm-dd
    parts: List[Part]

@dataclass
class Preferences:
    daily_hour_cap: int            
    weekly_study_days: int         
    avoid_days: Optional[list] = None   