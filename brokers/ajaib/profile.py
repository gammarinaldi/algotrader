import requests

def call(access_token):
    try:
        url = "https://ht2.ajaib.co.id/api/v2/stock/profile"

        payload={}

        headers = {
            'authority': 'ht2.ajaib.co.id',
            'accept': '*/*',
            'accept-language': 'id',
            'authorization': access_token,
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://invest.ajaib.co.id',
            'referer': 'https://invest.ajaib.co.id/',
            'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
            'x-ht-ver-id': '0322b9396fc0f476309aeafbbbe4e72d210e5c8f5815abf1fde7503b9126086e3e6d000a5f255765e8db3489c563a8fa950870c8920099ba073a08590d3da722',
            'x-platform': 'WEB',
            'x-product': 'stock-mf'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        return response
    except requests.exceptions.HTTPError as errh:
        return "Http Error: ", errh
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting: ", errc
    except requests.exceptions.Timeout as errt:
        return "Timeout Error: ", errt
    except requests.exceptions.RequestException as err:
        return "Oops.. Something Else: ", err
