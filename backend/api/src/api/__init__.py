import uvicorn
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    uvicorn.run("api.api:app", host="0.0.0.0", port=3001)
