import requests

def call(email, password):
    try:
        url = f"https://api.stockbit.com/v2.4/login?user={email}&password={password}"
        print(email, password)
        payload={}
        headers = {}
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