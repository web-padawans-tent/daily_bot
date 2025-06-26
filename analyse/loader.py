from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
MERCHANT_ACCOUNT = os.getenv("MERCHANT_ACCOUNT")
MERCHANT_DOMAIN = os.getenv("MERCHANT_DOMAIN")
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")
MERCHANT_PASSWORD = os.getenv("MERCHANT_PASSWORD")
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')
CHANNEL_LINK = os.getenv('CHANNEL_LINK')
