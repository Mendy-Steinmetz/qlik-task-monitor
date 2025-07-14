import requests
from requests_ntlm import HttpNtlmAuth
import logging
import urllib3
import random
import string
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from models import TaskDetails

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Qlik task statuses that indicate failure
ERROR_STATUSES = {4, 5, 8, 11}


class QlikAPIClient:
    """
    Client for interacting with Qlik Sense QRS API to fetch and filter failed tasks.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.settings = config['settings']
        self.server = config['qlik_sense']['server']
        self.user_directory = config['qlik_sense']['user_directory']
        self.user_id = config['qlik_sense']['user_id']
        self.password = config['qlik_sense']['password']
        self.default_email = config['email'].get('receiver_email')
        self.verbosity = self.settings.get('api_debug_output', False)

        # Retry configuration
        self.max_retries = self.settings.get('api_max_retries', 3)
        self.retry_delay = self.settings.get('api_retry_delay', 5)
        self.request_timeout = self.settings.get('api_timeout', 30)

        self.session = requests.Session()
        self.session.auth = HttpNtlmAuth(f"{self.user_directory}\\{self.user_id}", self.password)

    def get_tasks(self) -> List[Dict[str, Any]]:
        """
        Fetch all tasks from Qlik Sense QRS API with retry logic.
        """
        self._warmup_session()  # Warmup call

        xrfkey = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        url = f"https://{self.server}/qrs/task/full?Xrfkey={xrfkey}"
        headers = {
            'X-Qlik-Xrfkey': xrfkey,
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) qlik-monitor-client'
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                logging.info(
                    f"Connecting to Qlik Sense QRS API at {url} with NTLM session (attempt {attempt}/{self.max_retries})")

                response = self.session.get(
                    url,
                    headers=headers,
                    verify=False,
                    timeout=self.request_timeout
                )

                if self.verbosity:
                    logging.debug(f"[API DEBUG] Response status code: {response.status_code}")
                    logging.debug(f"[API DEBUG] Response headers: {response.headers}")
                    logging.debug(f"[API DEBUG] Response text: {response.text}")

                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError:
                    logging.error(f"Invalid JSON response received: {response.text}")
                    if attempt < self.max_retries:
                        logging.warning(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue
                    return []

                logging.info(f"Successfully fetched {len(data)} tasks from Qlik Sense API")
                return data

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:

                logging.warning(f"Attempt {attempt} failed: {str(e)}")

                if attempt < self.max_retries:
                    wait_time = self.retry_delay * attempt  # Exponential backoff
                    logging.warning(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"All {self.max_retries} attempts failed. Last error: {e}")

            except Exception as e:
                logging.error(f"Unexpected error during API call: {e}", exc_info=True)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    break

        return []

    def get_failed_tasks(self) -> List[TaskDetails]:
        """
        Filter failed tasks and return them as TaskDetails objects.
        """
        tasks = self.get_tasks()
        if not tasks:
            logging.warning("No tasks retrieved from API - returning empty list")
            return []

        failed_tasks = []

        for task in tasks:
            task_name = task.get('name', 'Unknown Task')
            result = task.get('operational', {}).get('lastExecutionResult', {})
            status_code = result.get('status')

            if status_code not in ERROR_STATUSES:
                logging.debug(f"Task '{task_name}' skipped: status {status_code}")
                continue

            stop_time = result.get('stopTime')
            timestamp = self._format_time(stop_time)
            interval = self._get_execution_interval(result, task.get('operational', {}))
            log_rel_path = result.get('scriptLogLocation', '')
            log_file_path = os.path.join(self.settings['log_archive_path'], log_rel_path) if log_rel_path else ''
            log_url = f"file://{log_file_path.replace('/', os.sep)}" if log_file_path else 'N/A'

            app_info = task.get('app', {})
            app_name = app_info.get('name', 'Unknown')
            stream_name = (app_info.get('stream') or {}).get('name', 'N/A')

            custom_emails = [
                prop.get('value') for prop in task.get('customProperties', [])
                if prop.get('definition', {}).get('name') == self.settings.get('custom_property_name', 'CS_Tasks')
                   and prop.get('value')
            ]
            recipients = custom_emails if custom_emails else [self.default_email]

            for email in recipients:
                failed_tasks.append(TaskDetails(
                    name=task_name,
                    id=task.get('id', 'Unknown ID'),
                    app_name=app_name,
                    stream=stream_name,
                    status=self._status_name(status_code),
                    log_url=log_url,
                    timestamp=timestamp,
                    execution_interval=interval,
                    log_file_path=log_file_path,
                    recipient=email
                ))

        return failed_tasks

    def _format_time(self, raw_time: str) -> str:
        """
        Convert ISO timestamp to local time string.
        """
        try:
            dt = datetime.fromisoformat(raw_time.replace('Z', '+00:00')).astimezone()
            return dt.replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
        except Exception:
            return 'N/A'

    def _get_execution_interval(self, result: Dict[str, Any], operational: Dict[str, Any]) -> str:
        """
        Calculate interval between start and next execution.
        """
        try:
            start = result.get('startTime')
            nxt = operational.get('nextExecution')
            if not start or not nxt:
                return 'N/A'

            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            nxt_dt = datetime.fromisoformat(nxt.replace('Z', '+00:00'))
            diff = nxt_dt - start_dt
            if diff.total_seconds() < 0:
                return 'N/A'

            rounded = timedelta(minutes=round(diff.total_seconds() / 60))
            return self._format_timedelta(rounded)
        except Exception:
            return 'N/A'

    def _format_timedelta(self, td: timedelta) -> str:
        """
        Format timedelta into human-readable string.
        """
        total_minutes = int(td.total_seconds() // 60)
        days, remainder = divmod(total_minutes, 1440)
        hours, minutes = divmod(remainder, 60)
        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes or not parts:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        return ", ".join(parts)

    def _status_name(self, status_code: int) -> str:
        """
        Map status code to human-readable name.
        """
        status_map = {
            4: "AbortInitiated",
            5: "Aborting",
            8: "FinishedFail",
            11: "Error"
        }
        return status_map.get(status_code, str(status_code))

    def _warmup_session(self):
        """
        Perform a GET /qrs/about call to warm up the Qlik session.
        """
        xrfkey = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        url = f"https://{self.server}/qrs/about?Xrfkey={xrfkey}"
        headers = {
            'X-Qlik-Xrfkey': xrfkey,
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) qlik-monitor-client'
        }

        try:
            response = self.session.get(url, headers=headers, verify=False, timeout=self.request_timeout)
            response.raise_for_status()
            logging.info("Qlik Sense warmup (GET /qrs/about) succeeded")
        except Exception as e:
            logging.warning(f"Warmup request to /qrs/about failed: {e}")
