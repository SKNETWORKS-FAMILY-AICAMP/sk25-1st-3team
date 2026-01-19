import os
from dotenv import load_dotenv

# Load environment variables from .env (local development)
load_dotenv()

DB_CONFIG = dict(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    charset=os.getenv("DB_CHARSET", "utf8mb4"),
)

FAQ_PAGE_SIZE = int(os.getenv("FAQ_PAGE_SIZE", 10))
EV_PAGE_SIZE = int(os.getenv("EV_PAGE_SIZE", 50))

EV_CHARGER_TABLE = "ev_charger"
CAR_MODEL_TABLE = "car_model"
