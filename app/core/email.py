from typing import Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from pathlib import Path
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings

class EmailManager:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_SSL_TLS=True,  # Keep only one SSL/TLS setting
            MAIL_STARTTLS=getattr(settings, "MAIL_STARTTLS", False),
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            USE_CREDENTIALS=True,
            TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates' / 'email',
            VALIDATE_CERTS=True,
        )
        self.fastmail = FastMail(self.conf)

    def create_verification_token(self, email: str) -> str:
        """Create a verification token for email verification"""
        expire = datetime.utcnow() + timedelta(hours=24)
        data = {
            "exp": expire,
            "email": email,
            "type": "email_verification"
        }
        return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")

    def create_password_reset_token(self, email: str) -> str:
        """Create a token for password reset"""
        expire = datetime.utcnow() + timedelta(hours=1)
        data = {
            "exp": expire,
            "email": email,
            "type": "password_reset"
        }
        return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")

    async def send_verification_email(self, email: EmailStr, token: str):
        """Send verification email to user"""
        verify_url = f"{settings.SERVER_HOST}/verify-email?token={token}"
        
        message = MessageSchema(
            subject="Verify your email",
            recipients=[email],
            template_body={
                "verify_url": verify_url,
                "expire_hours": 24
            },
            subtype="html"
        )
        
        await self.fastmail.send_message(
            message,
            template_name="verification.html"
        )

    async def send_password_reset_email(self, email: EmailStr, token: str):
        """Send password reset email"""
        reset_url = f"{settings.SERVER_HOST}/reset-password?token={token}"
        
        message = MessageSchema(
            subject="Reset your password",
            recipients=[email],
            template_body={
                "reset_url": reset_url,
                "expire_hours": 1
            },
            subtype="html"
        )
        
        await self.fastmail.send_message(
            message,
            template_name="password_reset.html"
        )

    async def send_password_change_notification(self, email: EmailStr):
        """Send notification when password is changed"""
        message = MessageSchema(
            subject="Your password has been changed",
            recipients=[email],
            template_body={
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            },
            subtype="html"
        )
        
        await self.fastmail.send_message(
            message,
            template_name="password_changed.html"
        )

    def verify_token(self, token: str, token_type: str) -> Optional[str]:
        """Verify a token and return the email if valid"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload["type"] != token_type:
                return None
            return payload["email"]
        except jwt.JWTError:
            return None

# Create an instance of EmailManager
email_manager = EmailManager()