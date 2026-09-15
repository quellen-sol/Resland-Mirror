import os

from dotenv import load_dotenv

load_dotenv()

AMQP_URL = os.getenv("AMQP_URL") or ""
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") or ""
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or ""
PG_URL = os.getenv("PG_URL") or ""
S3_RESUME_BUCKET = os.getenv("S3_RESUME_BUCKET") or ""
RESUME_PARSER_MODEL = os.getenv("RESUME_PARSER_MODEL") or ""
SUGGESTIONS_MODEL = os.getenv("SUGGESTIONS_MODEL") or ""
