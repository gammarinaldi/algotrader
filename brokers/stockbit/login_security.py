import requests
import json

def call(user, security_token):
    try:
        url = "https://carina.stockbit.com/auth/v2/login"
                
        payload = json.dumps({
            "login_token": security_token,
            "pin": user['pin']
        })
        
        headers = {
           'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7',
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
