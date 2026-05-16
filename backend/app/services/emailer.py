import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# ─────────────────────────────────────────────
# EMAIL CONFIGURATION
# Set SMTP_PASSWORD env var to your Gmail App Password
# (Google Account → Security → 2-Step → App Passwords)
# ─────────────────────────────────────────────
SMTP_SERVER   = os.getenv("SMTP_SERVER",   "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "paramveercse@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")          # Set via env var
ALERT_EMAIL   = os.getenv("ALERT_EMAIL",  "paramveercse@gmail.com")


def send_pothole_email(lat: float, lon: float, severity: str, image_path: str) -> None:
    """
    Send an automated road-damage alert email.
    Runs synchronously — call via trigger_pothole_report() to avoid blocking.
    """
    maps_url   = f"https://www.google.com/maps?q={lat},{lon}"
    sev_upper  = severity.upper()
    sev_color  = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(sev_upper, "#6b7280")

    # ── Simulation mode when no password is configured ──────────────
    if not SMTP_PASSWORD:
        print(f"\n[EMAIL SIMULATION] → {ALERT_EMAIL}")
        print(f"[EMAIL SIMULATION] Subject : 🚨 {sev_upper} Severity Road Damage Detected")
        print(f"[EMAIL SIMULATION] Location: {maps_url}")
        print(f"[EMAIL SIMULATION] Image   : {image_path}\n")
        return

    try:
        msg = MIMEMultipart("related")
        msg["From"]    = f"DriveSafe Alert <{SMTP_USERNAME}>"
        msg["To"]      = ALERT_EMAIL
        msg["Subject"] = f"🚨 {sev_upper} Severity Road Damage Detected — DriveSafe"

        html_body = f"""
        <html>
          <body style="margin:0;padding:0;background:#0a0d14;font-family:'Inter',Arial,sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="max-width:600px;margin:32px auto;background:#111827;
                          border:1px solid #1a2540;border-radius:4px;overflow:hidden;">

              <!-- Header -->
              <tr>
                <td style="background:linear-gradient(135deg,#00CFFF,#0099CC);
                           padding:24px 28px;text-align:left;">
                  <span style="font-size:11px;font-weight:700;letter-spacing:0.15em;
                               color:#000;text-transform:uppercase;font-family:monospace;">
                    ⬡ DriveSafe · Autonomous Road Intelligence
                  </span>
                  <h1 style="margin:8px 0 0;font-size:22px;font-weight:800;color:#000;">
                    Road Damage Alert
                  </h1>
                </td>
              </tr>

              <!-- Severity Banner -->
              <tr>
                <td style="background:{sev_color}18;border-bottom:2px solid {sev_color};
                           padding:16px 28px;">
                  <span style="font-family:monospace;font-size:11px;font-weight:700;
                               letter-spacing:0.12em;text-transform:uppercase;color:{sev_color};">
                    ● {sev_upper} SEVERITY
                  </span>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:24px 28px;color:#e8f0fe;">
                  <p style="font-size:14px;color:#8899bb;margin:0 0 20px;">
                    The DriveSafe AI system has detected road damage requiring attention.
                  </p>

                  <table width="100%" cellpadding="8" cellspacing="0"
                         style="background:#0e1220;border:1px solid #1a2540;border-radius:2px;">
                    <tr>
                      <td style="font-family:monospace;font-size:10px;color:#8899bb;
                                 letter-spacing:0.1em;text-transform:uppercase;width:120px;">
                        Severity
                      </td>
                      <td style="font-family:monospace;font-size:14px;
                                 font-weight:700;color:{sev_color};">
                        {sev_upper}
                      </td>
                    </tr>
                    <tr style="border-top:1px solid #1a2540;">
                      <td style="font-family:monospace;font-size:10px;color:#8899bb;
                                 letter-spacing:0.1em;text-transform:uppercase;">
                        Coordinates
                      </td>
                      <td style="font-family:monospace;font-size:12px;color:#e8f0fe;">
                        {lat:.6f}, {lon:.6f}
                      </td>
                    </tr>
                    <tr style="border-top:1px solid #1a2540;">
                      <td style="font-family:monospace;font-size:10px;color:#8899bb;
                                 letter-spacing:0.1em;text-transform:uppercase;">
                        Maps Link
                      </td>
                      <td>
                        <a href="{maps_url}"
                           style="color:#00CFFF;font-size:12px;font-weight:600;">
                          View on Google Maps →
                        </a>
                      </td>
                    </tr>
                  </table>

                  <p style="font-size:12px;color:#334466;margin:20px 0 0;">
                    This is an automated alert from the DriveSafe Road Intelligence System.
                    Sent from: {SMTP_USERNAME}
                  </p>
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="padding:14px 28px;border-top:1px solid #1a2540;
                           font-family:monospace;font-size:9px;color:#334466;
                           letter-spacing:0.08em;text-transform:uppercase;">
                  DRIVESAFE · AI ROAD MONITORING · {lat:.4f},{lon:.4f}
                </td>
              </tr>
            </table>
          </body>
        </html>
        """

        alt  = MIMEMultipart("alternative")
        alt.attach(MIMEText(html_body, "html"))
        msg.attach(alt)

        # Attach photo if it exists
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as fh:
                img = MIMEImage(fh.read(), name=os.path.basename(image_path))
            msg.attach(img)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] Alert sent to {ALERT_EMAIL} for {sev_upper} damage at {lat:.5f},{lon:.5f}")

    except Exception as exc:
        print(f"[EMAIL] Failed: {exc}")


def trigger_pothole_report(lat: float, lon: float, severity: str, image_path: str) -> None:
    """Fire-and-forget: sends email in background thread so API is non-blocking."""
    t = threading.Thread(
        target=send_pothole_email,
        args=(lat, lon, severity, image_path),
        daemon=True,
    )
    t.start()
