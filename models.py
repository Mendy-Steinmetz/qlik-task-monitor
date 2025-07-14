# qlik_monitor/models.py
from dataclasses import dataclass

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
