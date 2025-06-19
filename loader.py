from dotenv import load_dotenv
import os
from commands import Database

load_dotenv()

db = Database('database.db')
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
MERCHANT_ACCOUNT = os.getenv("MERCHANT_ACCOUNT")
MERCHANT_DOMAIN = os.getenv("MERCHANT_DOMAIN")
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")
