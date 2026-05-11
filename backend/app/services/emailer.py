import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Hardcoded dummy config for demo purposes, override with env vars if needed
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "noreply@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "dummy_app_password")
MUNICIPAL_EMAIL = os.getenv("MUNICIPAL_EMAIL", "municipal@example.com")

def send_pothole_email(lat, lon, severity, image_path):
    """
    Sends an automated email to the municipal authority.
    This function runs synchronously, so it should be called in a background thread.
    """
    if SMTP_PASSWORD == "dummy_app_password":
        print(f"\n[EMAIL SIMULATION] Would send email to {MUNICIPAL_EMAIL}")
        print(f"[EMAIL SIMULATION] Subject: URGENT: {severity.upper()} Severity Pothole Detected")
        print(f"[EMAIL SIMULATION] Location: https://www.google.com/maps?q={lat},{lon}")
        print(f"[EMAIL SIMULATION] Attached: {image_path}\n")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = MUNICIPAL_EMAIL
        msg['Subject'] = f"URGENT: {severity.upper()} Severity Pothole Detected"

        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #ef4444;">Automated Pothole Report</h2>
                <p>The AI Road Monitoring system has detected a pothole requiring attention.</p>
                <ul>
                    <li><b>Severity:</b> {severity.upper()}</li>
                    <li><b>Location:</b> <a href="{maps_link}">View on Google Maps</a> ({lat}, {lon})</li>
                </ul>
                <p>A visual proof image has been attached to this email.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(image_path))
            msg.attach(image)
            
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Automated report sent for pothole at {lat}, {lon}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def trigger_pothole_report(lat, lon, severity, image_path):
    """
    Spawns a background thread to send the email without blocking the API.
    """
    thread = threading.Thread(target=send_pothole_email, args=(lat, lon, severity, image_path))
    thread.start()
