import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

class EmailClient:
    """Email client for notifications and approvals"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender = os.getenv("EMAIL_SENDER")
        self.password = os.getenv("EMAIL_PASSWORD")
    
    def send_email(
        self, 
        recipient: str, 
        subject: str, 
        body_html: str,
        attachments: list = None
    ):
        """Send HTML email"""
        if not self.sender or not self.password:
            print("Email credentials not configured. Skipping email send.")
            return
        
        msg = MIMEMultipart('alternative')
        msg['From'] = self.sender
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Attach HTML body
        msg.attach(MIMEText(body_html, 'html'))
        
        # Attach files if provided
        if attachments:
            for filepath in attachments:
                self._attach_file(msg, filepath)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def _attach_file(self, msg: MIMEMultipart, filepath: str):
        """Attach file to email"""
        path = Path(filepath)
        if not path.exists():
            return
        
        with open(path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={path.name}'
            )
            msg.attach(part)
    
    def send_approval_request(self, report_html: str, recipient: str):
        """Send weekly approval email"""
        week_id = datetime.now().strftime('%Y-W%W')
        subject = f"Weekly News Digest Approval - Week {week_id}"
        self.send_email(recipient, subject, report_html)
