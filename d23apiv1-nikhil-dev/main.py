import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import uvicorn

from bot.whatsapp.webhook import router as whatsapp_router
from bot.services.reminder_service import ReminderService
from bot.services import (
    start_horoscope_scheduler,
    stop_horoscope_scheduler,
    start_transit_service,
    stop_transit_service,
)
from bot.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting D23Bot services...")

    # Start reminder scheduler
    ReminderService.start_scheduler()

    # Start subscription services (horoscope & transit)
    if not settings.LITE_MODE:
        try:
            await start_horoscope_scheduler()
            await start_transit_service()
            logger.info("Horoscope and Transit services started")
        except Exception as e:
            logger.warning(f"Could not start subscription services: {e}")
    else:
        logger.info("Running in LITE_MODE - subscription services disabled")

    yield

    # Shutdown
    logger.info("Shutting down D23Bot services...")
    ReminderService.shutdown_scheduler()

    if not settings.LITE_MODE:
        await stop_horoscope_scheduler()
        await stop_transit_service()


app = FastAPI(lifespan=lifespan, title="D23Bot", version="2.0.0")


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "D23Bot",
        "version": "2.0.0",
        "features": [
            "Daily Horoscope Subscription",
            "Transit Alerts",
            "22 Indian Languages",
            "Life Predictions",
        ]
    }


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "lite_mode": settings.LITE_MODE,
    }


@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    """Privacy Policy page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - D23 AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.7;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 50px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .logo p {
            color: #666;
            font-size: 1.1em;
        }
        h2 {
            color: #667eea;
            margin: 35px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }
        h3 {
            color: #444;
            margin: 25px 0 10px 0;
        }
        p { margin: 12px 0; color: #555; }
        ul {
            margin: 15px 0 15px 25px;
            color: #555;
        }
        li { margin: 8px 0; }
        .highlight {
            background: linear-gradient(135deg, #667eea15, #764ba215);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            margin: 20px 0;
        }
        .contact-box {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-top: 30px;
        }
        .contact-box a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        .contact-box a:hover { text-decoration: underline; }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #888;
            font-size: 0.9em;
        }
        .badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>D23 AI</h1>
            <p>Bharat's WhatsApp AI Assistant</p>
        </div>

        <h2>Privacy Policy</h2>
        <p><strong>Effective Date:</strong> December 26, 2025</p>
        <p><strong>Last Updated:</strong> December 26, 2025</p>

        <p>Welcome to D23 AI ("we," "our," or "us"). This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our WhatsApp-based AI assistant service.</p>

        <div class="highlight">
            <strong>Our Commitment:</strong> We respect your privacy and are committed to protecting your personal data. We only collect information necessary to provide our services.
        </div>

        <h2>1. Information We Collect</h2>

        <h3>1.1 Information You Provide</h3>
        <ul>
            <li><strong>Phone Number:</strong> Your WhatsApp phone number for communication</li>
            <li><strong>Messages:</strong> Text messages you send to our bot</li>
            <li><strong>Birth Details:</strong> Date, time, and place of birth (for astrology services)</li>
            <li><strong>Name:</strong> Your name if provided for personalized services</li>
            <li><strong>Preferences:</strong> Language preference and subscription choices</li>
        </ul>

        <h3>1.2 Automatically Collected Information</h3>
        <ul>
            <li>Message timestamps</li>
            <li>Interaction patterns with the bot</li>
            <li>Service usage statistics</li>
        </ul>

        <h2>2. How We Use Your Information</h2>
        <p>We use the collected information to:</p>
        <ul>
            <li>Provide personalized astrology readings and horoscopes</li>
            <li>Deliver daily horoscope subscriptions</li>
            <li>Send planetary transit alerts</li>
            <li>Process utility requests (weather, news, PNR status, etc.)</li>
            <li>Improve our AI responses and services</li>
            <li>Send reminders you have set</li>
            <li>Communicate service updates</li>
        </ul>

        <h2>3. Data Storage & Security</h2>
        <div class="highlight">
            <span class="badge">Secure</span>
            <span class="badge">Encrypted</span>
            <span class="badge">Protected</span>
            <p style="margin-top: 15px;">Your data is stored securely with industry-standard encryption. We implement appropriate technical and organizational measures to protect your personal information.</p>
        </div>
        <ul>
            <li>Data is encrypted in transit and at rest</li>
            <li>Access to personal data is restricted to authorized personnel</li>
            <li>Regular security audits and updates</li>
            <li>Secure cloud infrastructure</li>
        </ul>

        <h2>4. Third-Party Services</h2>
        <p>We use the following third-party services to provide our functionality:</p>
        <ul>
            <li><strong>WhatsApp Business API:</strong> For message delivery (Meta's privacy policy applies)</li>
            <li><strong>OpenAI:</strong> For AI-powered responses</li>
            <li><strong>Weather APIs:</strong> For weather information</li>
            <li><strong>News APIs:</strong> For news updates</li>
            <li><strong>Indian Railways API:</strong> For PNR and train status</li>
        </ul>
        <p>These services have their own privacy policies, and we encourage you to review them.</p>

        <h2>5. Data Retention</h2>
        <p>We retain your data for as long as necessary to provide our services:</p>
        <ul>
            <li><strong>Messages:</strong> Stored temporarily for context (up to 30 days)</li>
            <li><strong>Birth Details:</strong> Retained until you request deletion</li>
            <li><strong>Subscriptions:</strong> Active until you unsubscribe</li>
            <li><strong>Usage Data:</strong> Anonymized after 90 days</li>
        </ul>

        <h2>6. Your Rights</h2>
        <p>You have the right to:</p>
        <ul>
            <li><strong>Access:</strong> Request a copy of your personal data</li>
            <li><strong>Correction:</strong> Update or correct your information</li>
            <li><strong>Deletion:</strong> Request deletion of your data</li>
            <li><strong>Opt-out:</strong> Unsubscribe from any services</li>
            <li><strong>Portability:</strong> Receive your data in a portable format</li>
        </ul>
        <p>To exercise these rights, send "DELETE MY DATA" or "MY DATA" to our WhatsApp bot, or contact us directly.</p>

        <h2>7. Children's Privacy</h2>
        <p>Our service is not intended for children under 13 years of age. We do not knowingly collect personal information from children under 13.</p>

        <h2>8. Changes to This Policy</h2>
        <p>We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date.</p>

        <h2>9. Contact Us</h2>
        <div class="contact-box">
            <p>If you have any questions about this Privacy Policy or our data practices, please contact us:</p>
            <ul style="list-style: none; margin-left: 0; margin-top: 15px;">
                <li><strong>WhatsApp:</strong> Send a message to our bot</li>
                <li><strong>Email:</strong> <a href="mailto:privacy@d23ai.in">privacy@d23ai.in</a></li>
                <li><strong>Website:</strong> <a href="https://d23ai.in">https://d23ai.in</a></li>
            </ul>
        </div>

        <div class="footer">
            <p>&copy; 2025 D23 AI. All rights reserved.</p>
            <p style="margin-top: 10px;">
                <a href="https://d23ai.in" style="color: #667eea; text-decoration: none;">Home</a> &nbsp;|&nbsp;
                <a href="/terms" style="color: #667eea; text-decoration: none;">Terms of Service</a>
            </p>
        </div>
    </div>
</body>
</html>
"""


@app.get("/terms", response_class=HTMLResponse)
def terms_of_service():
    """Terms of Service page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - D23 AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.7;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 50px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .logo p {
            color: #666;
            font-size: 1.1em;
        }
        h2 {
            color: #667eea;
            margin: 35px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }
        p { margin: 12px 0; color: #555; }
        ul {
            margin: 15px 0 15px 25px;
            color: #555;
        }
        li { margin: 8px 0; }
        .highlight {
            background: linear-gradient(135deg, #667eea15, #764ba215);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #888;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>D23 AI</h1>
            <p>Bharat's WhatsApp AI Assistant</p>
        </div>

        <h2>Terms of Service</h2>
        <p><strong>Effective Date:</strong> December 26, 2025</p>

        <p>By using D23 AI WhatsApp bot, you agree to these Terms of Service.</p>

        <h2>1. Service Description</h2>
        <p>D23 AI is a WhatsApp-based AI assistant providing:</p>
        <ul>
            <li>Vedic astrology readings and horoscopes</li>
            <li>Daily horoscope subscriptions</li>
            <li>Planetary transit alerts</li>
            <li>Utility services (weather, news, train status)</li>
            <li>General AI chat assistance</li>
        </ul>

        <h2>2. Acceptable Use</h2>
        <p>You agree NOT to:</p>
        <ul>
            <li>Use the service for illegal purposes</li>
            <li>Send spam or abusive messages</li>
            <li>Attempt to hack or disrupt the service</li>
            <li>Impersonate others</li>
            <li>Use automated systems to abuse the service</li>
        </ul>

        <h2>3. Astrology Disclaimer</h2>
        <div class="highlight">
            <strong>Important:</strong> Astrological readings are for entertainment and informational purposes only. They should not be used as a substitute for professional advice (medical, legal, financial, etc.). We make no guarantees about the accuracy of predictions.
        </div>

        <h2>4. Service Availability</h2>
        <p>We strive to provide uninterrupted service but do not guarantee 100% uptime. We may modify, suspend, or discontinue the service at any time.</p>

        <h2>5. Limitation of Liability</h2>
        <p>D23 AI is provided "as is" without warranties. We are not liable for any damages arising from the use of our service.</p>

        <h2>6. Changes to Terms</h2>
        <p>We may update these terms at any time. Continued use of the service constitutes acceptance of the updated terms.</p>

        <h2>7. Contact</h2>
        <p>For questions about these terms, contact us at <a href="mailto:support@d23ai.in" style="color: #667eea;">support@d23ai.in</a></p>

        <div class="footer">
            <p>&copy; 2025 D23 AI. All rights reserved.</p>
            <p style="margin-top: 10px;">
                <a href="https://d23ai.in" style="color: #667eea; text-decoration: none;">Home</a> &nbsp;|&nbsp;
                <a href="/privacy" style="color: #667eea; text-decoration: none;">Privacy Policy</a>
            </p>
        </div>
    </div>
</body>
</html>
"""


app.include_router(whatsapp_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9002)
