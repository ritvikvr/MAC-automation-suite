# emailer.py
import smtplib
from email.message import EmailMessage

def send_email(to_addrs, subject, body, smtp_server, smtp_port, username, password):
    """
    Sends an email. Supports Gmail SMTP.
    """
    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg.set_content(body)
    # Connect to SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.send_message(msg)
    server.quit()
    print(f"Email sent to {to_addrs}.")
    
# Example usage (configure in config.yaml):
# send_email(["friend@example.com"], "Test", "Hello from Python", 
#            "smtp.gmail.com", 587, "you@gmail.com", "app_password")
