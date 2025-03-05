import os
from dotenv import load_dotenv

load_dotenv(override=True)

list = [{"email": os.getenv('USERNAME'), "password": os.getenv('PASSWORD'), "pin": os.getenv('PIN')}]
