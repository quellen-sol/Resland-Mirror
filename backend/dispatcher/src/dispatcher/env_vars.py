import os

from dotenv import load_dotenv

load_dotenv()

AMQP_URL = os.getenv("AMQP_URL")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
PG_URL = os.getenv("PG_URL")
S3_RESUME_BUCKET = os.getenv("S3_RESUME_BUCKET")
RESUME_PARSER_MODEL = os.getenv("RESUME_PARSER_MODEL")
