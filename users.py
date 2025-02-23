import os
from dotenv import load_dotenv

load_dotenv()

list = [{"email": os.getenv('AJ_USER'), "password": os.getenv('AJ_PASS'), "pin": os.getenv('AJ_PIN')}]
