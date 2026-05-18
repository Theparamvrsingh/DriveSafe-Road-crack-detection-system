import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "paramveercse@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "paramveercse@gmail.com")


def is_email_configured() -> bool:
    return bool(SMTP_PASSWORD and SMTP_PASSWORD.strip())


def get_email_status() -> dict:
    return {
        "configured": is_email_configured(),
        "recipient": ALERT_EMAIL,
        "from": SMTP_USERNAME,
    }


def send_pothole_email(lat: float, lon: float, severity: str, image_path: str) -> dict:
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    sev_upper = severity.upper()
    sev_color = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(
        sev_upper, "#6b7280"
    )

    if not is_email_configured():
        print(f"\n[EMAIL SIMULATION] → {ALERT_EMAIL}")
        print(f"[EMAIL SIMULATION] Subject : {sev_upper} Severity Road Damage Detected")
        print(f"[EMAIL SIMULATION] Location: {maps_url}")
        print(f"[EMAIL SIMULATION] Image   : {image_path}\n")
        return {"sent": False, "simulated": True, "recipient": ALERT_EMAIL}

    try:
        msg = MIMEMultipart("related")
        msg["From"] = f"DriveSafe Alert <{SMTP_USERNAME}>"
        msg["To"] = ALERT_EMAIL
        msg["Subject"] = f"{sev_upper} Severity Road Damage Detected — DriveSafe"

        html_body = f"""
        <html>
          <body style="margin:0;padding:0;background:#0a0d14;font-family:Arial,sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="max-width:600px;margin:32px auto;background:#111827;
                          border:1px solid #1a2540;border-radius:4px;">
              <tr>
                <td style="background:linear-gradient(135deg,#00CFFF,#0099CC);padding:24px 28px;">
                  <h1 style="margin:0;font-size:22px;color:#000;">Road Damage Alert</h1>
                  <p style="margin:8px 0 0;font-size:12px;color:#000;">DriveSafe · Autonomous Road Intelligence</p>
                </td>
              </tr>
              <tr>
                <td style="padding:20px 28px;color:#e8f0fe;">
                  <p style="font-size:14px;color:#8899bb;">AI-detected road damage requiring attention.</p>
                  <p><b style="color:{sev_color}">{sev_upper}</b> severity at {lat:.6f}, {lon:.6f}</p>
                  <p><a href="{maps_url}" style="color:#00CFFF;">View on Google Maps</a></p>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html_body, "html"))
        msg.attach(alt)

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as fh:
                img = MIMEImage(fh.read(), name=os.path.basename(image_path))
            msg.attach(img)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] Alert sent to {ALERT_EMAIL} at {lat:.5f},{lon:.5f}")
        return {"sent": True, "simulated": False, "recipient": ALERT_EMAIL}

    except Exception as exc:
        print(f"[EMAIL] Failed: {exc}")
        return {"sent": False, "simulated": False, "recipient": ALERT_EMAIL, "error": str(exc)}


def trigger_pothole_report(lat: float, lon: float, severity: str, image_path: str) -> None:
    t = threading.Thread(
        target=send_pothole_email,
        args=(lat, lon, severity, image_path),
        daemon=True,
    )
    t.start()
