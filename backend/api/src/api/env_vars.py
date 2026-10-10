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
# Machine-to-machine app for the Auth0 Management API (read:users,
# delete:users) — account export reads the login profile, account deletion
# deletes it. Deletion refuses to start while these are unset.
AUTH0_MGMT_CLIENT_ID = os.getenv("AUTH0_MGMT_CLIENT_ID") or ""
AUTH0_MGMT_CLIENT_SECRET = os.getenv("AUTH0_MGMT_CLIENT_SECRET") or ""
# Only needed when AUTH0_DOMAIN is a custom domain: the Management API is
# served on the tenant's canonical <tenant>.<region>.auth0.com domain.
AUTH0_MGMT_DOMAIN = os.getenv("AUTH0_MGMT_DOMAIN") or ""

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
