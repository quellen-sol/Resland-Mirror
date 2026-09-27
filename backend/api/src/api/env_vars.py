import os

from dotenv import load_dotenv

load_dotenv()

S3_RESUME_BUCKET = os.getenv("S3_RESUME_BUCKET") or ""
AMQP_URL = os.getenv("AMQP_URL") or ""
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") or ""
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or ""
PG_URL = os.getenv("PG_URL") or ""
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN") or ""
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE") or ""

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY") or ""
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET") or ""
# Where Stripe Checkout sends the browser back after payment.
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL") or "http://localhost:3000"

# Legacy bootstrap: seeds site_settings.maintenance_mode when the row is first
# created, so an env-paused deploy stays paused. Afterwards /admin owns the flag.
MAINTENANCE_MODE = (os.getenv("MAINTENANCE_MODE") or "").strip().lower() in {
    "1",
    "true",
    "on",
    "yes",
}
