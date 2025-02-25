import requests
import json
import brokers.ajaib.order_book
import lib
from math import floor
from datetime import date, timedelta

today = date.today()

def create_buy(access_token, emiten, buy_price, amount):
    res = brokers.ajaib.order_book.call(access_token, emiten)
    if res.status_code == 200:
        # Buy price by HAKA
        # data = res.json()
        # order_price = data["sell_side"]["items"][0]["price"]

        # Buy price by Close Price
        order_price = buy_price

        lot = floor(( amount / float(order_price)) / 100)

        try:
            url = "https://ht2.ajaib.co.id/api/v1/stock/buy/"

            payload = json.dumps({
                "ticker_code": emiten,
                "price": order_price,
                "lot": lot,
                "board": "0RG",
                "period": "day"
            })

            headers = {
                'accept': '*/*',
                'accept-language': 'id',
                'authorization': access_token,
                'content-type': 'application/json',
                'dnt': '1',
                'origin': 'https://invest.ajaib.co.id',
                'priority': 'u=1, i',
                'referer': 'https://invest.ajaib.co.id/',
                'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                'x-device-name': 'Web Chrome (Windows)',
                'x-device-signature': '3137997643',
                'x-ht-ver-id': '0322b9396fc0f476309aeafbbbe4e72d210e5c8f5815abf1fde7503b9126086e3e6d000a5f255765e8db3489c563a8fa950870c8920099ba073a08590d3da722',
                'x-platform': 'WEB',
                'x-product': 'stock-mf'
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
    else:
        return "Create buy error: Get order book error: ", res

def create_sell(access_token, emiten, value, lot, comparator):
    try:
        url = "https://ht2.ajaib.co.id/api/v1/stock/auto-trading/?account_type=REG"
        
        start = today + timedelta(days=1)
        end = start + timedelta(days=30)
        start_date = start.strftime("%Y-%m-%d")
        end_date = end.strftime("%Y-%m-%d")
        
        trigger_price = int(value)
        order_price = int(value) - lib.tick(int(value))
        
        payload = json.dumps({
            "code": emiten,
            "side": "SELL",
            "criterion": "PRICE",
            "comparator": comparator,
            "value": trigger_price,
            "order_price": order_price,
            "lot": int(lot),
            "start_date": start_date,
            "end_date": end_date,
            "expiry": "day"
        })

        headers = {
            'accept': '*/*',
            'accept-language': 'id',
            'authorization': access_token,
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://invest.ajaib.co.id',
            'priority': 'u=1, i',
            'referer': 'https://invest.ajaib.co.id/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'x-device-name': 'Web Chrome (Windows)',
            'x-device-signature': '3137997643',
            'x-ht-ver-id': '0322b9396fc0f476309aeafbbbe4e72d210e5c8f5815abf1fde7503b9126086e3e6d000a5f255765e8db3489c563a8fa950870c8920099ba073a08590d3da722',
            'x-platform': 'WEB',
            'x-product': 'stock-mf'
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
