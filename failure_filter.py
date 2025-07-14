from datetime import datetime, timedelta
import csv
import logging
from typing import Dict, Tuple

def load_previous_failures(path: str) -> Dict[Tuple[str, str], datetime]:
    """
    Load the most recent Run Time per (Task ID, Timestamp) from the failure history CSV.

    Args:
        path (str): Path to the CSV file.

    Returns:
        dict: Mapping of (task_id, timestamp) -> latest run_time
    """
    history = {}
    try:
        with open(path, newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            for row in rows:
                task_id = row.get('Task ID')
                failure_time = row.get('Timestamp')
                run_time_str = row.get('Run Time')
                if task_id and failure_time and run_time_str:
                    key = (task_id, failure_time.strip()[:16])
                    try:
                        run_time = datetime.strptime(run_time_str.strip(), "%Y-%m-%d %H:%M:%S")
                        if key not in history or run_time > history[key]:
                            history[key] = run_time
                    except ValueError:
                        continue
    except FileNotFoundError:
        logging.info(f"No previous failure history file found at {path}")
    return history


def should_notify(task, previous_failures: Dict[Tuple[str, str], datetime], reminder_hours: int) -> bool:
    """
    Determine whether a notification should be sent for a failed task.

    Args:
        task: TaskDetails object with task metadata.
        previous_failures: Dictionary mapping (task_id, timestamp) to last notification datetime.
        reminder_hours: Minimum hours between repeated notifications.

    Returns:
        bool: True if a notification should be sent, False otherwise.
    """
    timestamp_key = task.timestamp.strip()[:16]  # Format: 'YYYY-MM-DD HH:MM'
    key = (task.id, timestamp_key)
    last_sent = previous_failures.get(key)

    if reminder_hours == 0:
        logging.info(f"reminder_hours=0 -> Always send notification for task '{task.name}'")
        return True

    logging.debug(f"Checking task: {task.name} | Key: {key} | Last sent: {last_sent}")

    if not last_sent:
        logging.info(f"First failure detected for task '{task.name}'")
        return True

    now = datetime.now().replace(second=0, microsecond=0)
    last_sent = last_sent.replace(tzinfo=None)

    elapsed = now - last_sent

    if elapsed >= timedelta(hours=reminder_hours):
        hours_elapsed = round(elapsed.total_seconds() / 3600, 2)
        logging.info(
            f"Reminder: Task '{task.name}' is over the threshold ({hours_elapsed} > {reminder_hours} hours)"
            f" – sending notification.")
        return True

    logging.info(f"Skipping repeated task failure notification for '{task.name}'"
                 f" (already sent at {last_sent.strftime('%Y-%m-%d %H:%M')})")
    return False
