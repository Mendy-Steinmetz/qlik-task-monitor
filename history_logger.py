# qlik_monitor/history_logger.py

from datetime import datetime
import csv
import os
import logging
from models import TaskDetails
from typing import List


class HistoryLogger:
    @staticmethod
    def log_failures(tasks: List[TaskDetails], config: dict):
        mode = config['settings'].get('failure_log_mode', 'csv')
        path = config['settings'].get('failure_log_path', 'task_failures.csv')

        if mode == 'csv':
            need_header = not os.path.isfile(path) or os.path.getsize(path) == 0
            run_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                with open(path, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    if need_header:
                        writer.writerow(
                            ['Run Time', 'Task ID', 'Task Name', 'App Name', 'Stream', 'Timestamp', 'Status',
                             'Execution Interval'])
                    for task in tasks:
                        writer.writerow(
                            [run_time, task.id, task.name, task.app_name, task.stream, task.timestamp, task.status,
                             task.execution_interval])
                logging.info(f"Logged {len(tasks)} failed task(s) to history file: {path}")
            except Exception as e:
                logging.error(f"Error writing to failure history file: {e}")