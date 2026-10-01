import logging
import smtplib
from email.message import EmailMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_verification_email(email: str, token: str) -> None:
    verification_link = f"{settings.frontend_url}/verify-email?token={token}"
    
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        logger.warning(
            "SMTP credentials not fully configured. Email not sent. "
            f"Verification link for {email}: {verification_link}"
        )
        return

    try:
        msg = EmailMessage()
        msg.set_content(
            f"Welcome to TourMate!\n\n"
            f"Please verify your email address by clicking the following link:\n"
            f"{verification_link}\n\n"
            f"If you did not create an account, please ignore this email."
        )

        msg["Subject"] = "Verify your TourMate account"
        msg["From"] = settings.smtp_from_email or settings.smtp_user
        msg["To"] = email

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            
        logger.info(f"Verification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")
        # We don't raise here to prevent breaking the registration flow 
        # completely if the email service goes down, but we could if needed.
