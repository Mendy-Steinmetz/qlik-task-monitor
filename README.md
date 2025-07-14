# Qlik Sense Task Monitor

A lightweight Python tool to monitor Qlik Sense tasks and send failure alerts via email.

---

## 🚀 Quick Start

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Mendy-Steinmetz/qlik-task-monitor.git
cd qlik_monitor
```

---

### 2️⃣ Configure

Copy the example configuration files and fill in your details:

```bash
cp config.example.yaml config.yaml
cp .env.example .env
```

---

### 3️⃣ Install Requirements

Make sure you have **Python 3.8+** installed.

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Run the Monitor

```bash
python monitor.py
```

---

## ⚙️ Configuration

### `.env.example`

```env
QLIK_SENSE_SERVER=your-qlik-server
QLIK_SENSE_USER_DIRECTORY=your-user-dir
QLIK_SENSE_USER_ID=your-user
QLIK_SENSE_PASSWORD=your-password

EMAIL_SENDER_USERNAME=your-email-user
EMAIL_SENDER_PASSWORD=your-email-password
```

---

### `config.example.yaml`

```yaml
logging:
  global_log_level: INFO
  log_file: qlik_monitor.log

email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender_email: your_sender_email@example.com
  receiver_email: default_receiver@example.com

settings:
  api_timeout: 30
  api_max_retries: 3
  api_retry_delay: 5
  log_archive_path: path_to_logs
  failure_log_path: task_failures.csv
  reminder_hours: 24
  custom_property_name: CS_Tasks
  api_debug_output: false
  dry_run: false
```

---

## 📂 Project Structure

```
qlik_monitor/
│
├─ monitor.py              # Main runner
├─ config_loader.py        # Loads config and .env
├─ email_notifier.py       # Sends emails
├─ failure_filter.py       # Handles duplicate failure filtering
├─ history_logger.py       # Logs failure history
├─ models.py                # TaskDetails dataclass
├─ qlik_api_client.py      # Handles Qlik API calls
│
├─ config.example.yaml
├─ .env.example
├─ requirements.txt
├─ README.md
├─ .gitignore
```

---

## 🧰 Requirements

Minimal dependencies:

```
requests
requests_ntlm
python-dotenv
PyYAML
```

Install via:

```bash
pip install -r requirements.txt
```

---

## 🏗️ Build EXE (Optional)

If you want to create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --name qlik_monitor monitor.py
```

Output will be in `dist/qlik_monitor.exe`

---

## 💡 Notes

- Logs are saved to `qlik_monitor.log`
- Failure history is tracked in `task_failures.csv`
- Use `dry_run: true` for testing without sending real emails

---

## 🙋‍♂️ Contact

Created and maintained by **Mendy Steinmetz**

Feel free to reach out for questions, suggestions, or collaboration:

- 📧 **Email:** mendy.bi.2023@gmail.com  
- 🔗 **LinkedIn:** [Mendy Steinmetz](https://www.linkedin.com/in/mendy-steinmetz/)

I’d love to hear your feedback and ideas!

---

## 📝 License

This project is licensed under the **MIT License**.  
Feel free to use, modify, and distribute as you wish.

