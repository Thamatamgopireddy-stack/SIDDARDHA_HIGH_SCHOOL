import logging

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


async def send_account_email(
    *,
    recipient: str,
    subject: str,
    body: str,
    settings: Settings,
) -> str:
    if (
        settings.email_provider_api_key is None
        or not settings.email_provider_api_key.get_secret_value().strip()
        or not settings.email_from_address.strip()
    ):
        return "not_configured"
    api_key = settings.email_provider_api_key.get_secret_value()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": settings.email_from_address,
                    "to": [recipient],
                    "subject": subject,
                    "text": body,
                },
            )
    except httpx.HTTPError as exc:
        logger.error(
            "Account email delivery failed",
            extra={"error_type": type(exc).__name__},
        )
        return "failed"
    if not response.is_success:
        logger.error(
            "Account email provider rejected a notification",
            extra={"status_code": response.status_code},
        )
        return "failed"
    return "sent"
