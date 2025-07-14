# qlik_monitor/email_notifier.py
from collections import defaultdict
import os
import logging
from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
from models import TaskDetails


class EmailNotifier:
    @staticmethod
    def notify(tasks: List[TaskDetails], config: dict):
        settings = config['settings']
        dry_run = settings.get('dry_run', False)
        grouped_tasks = defaultdict(list)
        attachment_paths = defaultdict(list)
        attachment_names = defaultdict(list)

        for task in tasks:
            grouped_tasks[task.recipient].append(task)
            if task.log_file_path:
                if os.path.isfile(task.log_file_path):
                                    attachment_paths[task.recipient].append(task.log_file_path)
                                    attachment_names[task.recipient].append(f"{task.name}.log")
                else:
                    logging.warning(f"Log file not found: {task.log_file_path}")

        for email, task_list in grouped_tasks.items():
            logging.debug(f"Building email for {email} with {len(task_list)} tasks")
            logging.debug(f"Attachments: {attachment_paths[email]}")
            subject = f"Qlik Sense Task Failure Alert ({len(task_list)} Task{'s' if len(task_list) > 1 else ''})"
            html_body = EmailNotifier._build_html(task_list, email)

            if dry_run:
                logging.info(f"DRY-RUN: Would send email to {email} with {len(task_list)} task(s) and {len(attachment_paths[email])} attachment(s)")
                continue

            EmailNotifier._send(config['email'], subject, html_body, email, attachment_paths[email], attachment_names[email])

    @staticmethod
    def _build_html(tasks: List[TaskDetails], recipient: str) -> str:
        rows = "".join(f"""
            <tr>
                <td>{t.name}</td><td>{t.app_name}</td><td>{t.stream}</td><td>{t.status}</td>
                <td>{t.timestamp}</td><td>{t.execution_interval}</td>
                <td><a href=\"{t.log_url}\">{t.name}.log</a></td>
            </tr>""" for t in tasks)
        return f"""
        <html><head><style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
        </style></head><body>
            <p>Hello {recipient},</p>
            <p>This is an automated alert for failed Qlik Sense task(s):</p>
            <table>
                <tr><th>Task Name</th><th>Application</th><th>Stream</th><th>Status</th><th>Failure Time</th><th>Execution Interval</th><th>Log Link</th></tr>
                {rows}
            </table>
            <p>Regards,<br>Qlik Monitor System</p>
        </body></html>"""

    @staticmethod
    def _send(email_cfg: dict, subject: str, html_body: str, recipient: str, attachments: list, attachment_names: list):
        msg = MIMEMultipart()
        msg['From'] = email_cfg['sender_email']
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))

        for i, file_path in enumerate(attachments):
            try:
                with open(file_path, 'rb') as file:
                    name = attachment_names[i] if i < len(attachment_names) else os.path.basename(file_path)
                    part = MIMEApplication(file.read(), Name=name)
                    part['Content-Disposition'] = f'attachment; filename="{name}"'
                    msg.attach(part)
            except Exception as e:
                logging.warning(f"Failed to attach file {file_path}: {e}")

        try:
            with smtplib.SMTP(email_cfg['smtp_server'], email_cfg['smtp_port']) as server:
                server.starttls()
                server.login(email_cfg['sender_username'], email_cfg['sender_password'])
                server.send_message(msg)
            logging.info(f"Email sent to {recipient}")
        except Exception as e:
            logging.error(f"Failed to send email to {recipient}: {e}")
