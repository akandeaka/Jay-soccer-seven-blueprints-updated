# email_sender.py
import smtplib
from email.message import EmailMessage

class EmailSender:
    def __init__(self, smtp_host, smtp_port, sender_email, sender_password):
        self.host = smtp_host
        self.port = smtp_port
        self.sender_email = sender_email
        self.password = sender_password

    def send_report(self, recipient_email: str, subject: str, content: str):
        """Dispatches text report to specified email."""
        if not self.sender_email or not self.password:
            print("⚠️ SMTP credentials not configured. Skipping email dispatch.")
            return False

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg.set_content(content)

        try:
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.sender_email, self.password)
                server.send_message(msg)
            print("✅ Email report dispatched successfully.")
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
