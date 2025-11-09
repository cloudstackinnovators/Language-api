import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "smtppro.zoho.com"
SMTP_PORT = 465
SMTP_LOGIN = "support@vocablab.net"
SMTP_KEY = "CvPc1yVTmjzW"  # ideally from env var

def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_LOGIN
    msg["To"] = to_email

    # ✅ Use SMTP_SSL for port 465 (no starttls)
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_LOGIN, SMTP_KEY)
        server.send_message(msg)
        print("✅ Email sent successfully to", to_email)
