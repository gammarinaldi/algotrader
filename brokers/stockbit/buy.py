import requests
import time
import json
import random
import string

def generate_ui_ref():
    # Get current timestamp in milliseconds
    timestamp = str(int(time.time() * 1000))
    
    # Generate a random string of 13 characters
    random_chars = ''.join(random.choices(string.ascii_letters, k=13))
    
    # Combine timestamp and random characters
    ui_ref = f"W{timestamp}{random_chars}"
    return ui_ref

def call(access_token_sekuritas, symbol, price, shares):
    try:
        url = "https://carina.stockbit.com/order/v2/buy"
        
        payload = json.dumps({
            "ui_ref": generate_ui_ref(),
            "symbol": symbol,
            "price": price,
            "shares": shares,
            "board_type": "RG",
            "is_gtc": False,
            "time_in_force": "0",
            "platform_order_type": "PLATFORM_ORDER_TYPE_LIMIT_DAY"
        })

        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7',
            'authorization': 'Bearer ' + access_token_sekuritas,
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://stockbit.com',
            'priority': 'u=1, i',
            'referer': 'https://stockbit.com/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        
        return response
    except requests.exceptions.HTTPError as errh:
        return "Http Error: ", errh
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting: ", errc
    except requests.exceptions.Timeout as errt:
        return "Timeout Error: ", errt
    except requests.exceptions.RequestException as err:
        return "Oops.. Something Else: ", err

