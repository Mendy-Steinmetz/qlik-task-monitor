# qlik_monitor/monitor.py
import os
import sys
import logging
from config_loader import ConfigLoader
from qlik_api_client import QlikAPIClient as TaskMonitor
from email_notifier import EmailNotifier
from history_logger import HistoryLogger
from models import TaskDetails
from failure_filter import load_previous_failures, should_notify
from typing import List


def setup_logging(log_file_path: str = None, log_level: str = 'INFO'):
    if not log_file_path:
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_file_path = os.path.join(exe_dir, 'qlik_monitor.log')

    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main():
    try:
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(
            os.path.abspath(__file__))
        config_path = os.path.join(exe_dir, 'config.yaml')

        if not os.path.exists(config_path):
            logging.error(f"Configuration file not found at: {config_path}")
            sys.exit(1)

        config = ConfigLoader().load(config_path)

        log_settings = config.get('logging', {})
        log_file = log_settings.get('log_file', 'qlik_monitor.log')
        if not os.path.isabs(log_file):
            log_file = os.path.join(exe_dir, log_file)
        log_level = log_settings.get('global_log_level', 'INFO')
        logger = setup_logging(log_file, log_level)

        logger.info("=" * 60)
        logger.info("Qlik Sense Task Monitor Started")

        monitor = TaskMonitor(config)
        failed_tasks: List[TaskDetails] = monitor.get_failed_tasks()

        previous_failures = load_previous_failures(config['settings'].get('failure_log_path', 'task_failures.csv'))
        reminder_hours = config['settings'].get('reminder_hours', 24)

        tasks_to_notify = []
        for task in failed_tasks:
            if should_notify(task, previous_failures, reminder_hours):
                tasks_to_notify.append(task)

        if tasks_to_notify:
            HistoryLogger.log_failures(tasks_to_notify, config)
            EmailNotifier.notify(tasks_to_notify, config)
        else:
            logger.info("No new task failures to notify.")

        logger.info("Qlik Sense Task Monitor Finished")
        logger.info("=" * 60)

    except Exception as e:
        logging.error(f"Critical error in main execution: {e}", exc_info=True)
        if getattr(sys, 'frozen', False):
            input("Press Enter to exit...")
        sys.exit(1)


if __name__ == '__main__':
    main()
