from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional

class IDCounter:
    def __init__(self, start_id=0):
        self.current_id = start_id

    def next_id(self):
        self.current_id += 1
        return self.current_id

task_id_generator = IDCounter()
project_id_generator = IDCounter()

@dataclass
class Task:
    id: int = field(default_factory=task_id_generator.next_id, init=False)
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.now, init=False)

@dataclass
class Project:
    id: int = field(default_factory=project_id_generator.next_id, init=False)
    name: str
    description: Optional[str] = None
    tasks: List['Task'] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now, init=False)
