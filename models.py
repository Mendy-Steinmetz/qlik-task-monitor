#/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class TaskDetails:
    name: str
    id: str
    app_name: str
    stream: str
    status: str
    log_url: str
    timestamp: str
    execution_interval: str
    log_file_path: str
    recipient: str
    last_failure_time: Optional[str] = None