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
