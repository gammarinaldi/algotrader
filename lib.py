# import brokers.ajaib.get_buying_power
# import brokers.ajaib.login
# import brokers.ajaib.logout
# import brokers.ajaib.order
# import brokers.ajaib.portfolio
# import brokers.ajaib.auto_trading_list
# import brokers.ajaib.delete_auto_trade
# import brokers.ajaib.get_pin_data
# import brokers.ajaib.validate_pin

import brokers.stockbit.cancel_smart_order
import brokers.stockbit.login
import brokers.stockbit.get_security_token
import brokers.stockbit.login_security
import brokers.stockbit.portfolio
import brokers.stockbit.get_buying_power
import brokers.stockbit.order_list
import brokers.stockbit.trade_list
import brokers.stockbit.buy
import brokers.stockbit.sell
import brokers.stockbit.logout
import brokers.stockbit.orderbook

import concurrent.futures
import csv
import telegram
import logging
import traceback
import os
import time
import users
import stocks
import asyncio
from math import floor

from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

LOG = []

class data_order():
    def __init__(self, emiten, buy_price, take_profit, cut_loss):
        self.emiten = emiten
        self.buy_price = buy_price
        self.take_profit = take_profit
        self.cut_loss = cut_loss

def get_env():
    return os.getenv('ENABLE_SIGNAL'), os.getenv('ENABLE_BUY'), os.getenv('ENABLE_SELL'), os.getenv('SELL_DELAY'), os.getenv('DIR_PATH') 

def get_dir_path():
    return os.getenv('DIR_PATH')

def get_tele_data():
    tele_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    tele_chat_ids = [os.getenv('TELEGRAM_CHAT_ID_WINA'), os.getenv('TELEGRAM_CHAT_ID_SINYALA')]
    tele_log_id = os.getenv('TELEGRAM_LOGGER_ID')

    return tele_bot_token, tele_chat_ids, tele_log_id

def get_tele_bot():
    tele_bot_token, tele_chat_ids, tele_log_id = get_tele_data()
    bot = telegram.Bot(token=tele_bot_token)
    return bot, tele_chat_ids, tele_log_id

def is_empty_csv(path):
    with open(path) as csvfile:
        reader = csv.reader(csvfile)
        for i, _ in enumerate(reader):
            if i:  # Found the second row
                return False
    return True

def get_result():
    dir_path = get_dir_path()
    with open(f"{dir_path}\\signals\\result.csv", "r") as file:
        csvreader = csv.reader(file)
        if is_empty_csv(f"{dir_path}\\signals\\result.csv") == False:
            next(csvreader, None)

            list = []
            for row in csvreader:
                emiten = row[0]
                if row[0].find(".JK") != -1:
                    emiten = emiten.replace(".JK", "")

                signal_date = row[1].split(" ")[0]
                # close = row[2]
                # change = row[3]
                # trx = row[4]
                buy_price = row[5]
                take_profit = row[6]
                cut_loss = row[7]
                list.append([emiten, signal_date, buy_price, take_profit, cut_loss])
            return list
        else:
            msg = "No signal for today"
            bot, tele_chat_ids, _ = get_tele_bot()
            if os.getenv('ENABLE_SIGNAL') == "1":
                send_msg_v2(bot, tele_chat_ids, msg)
            return msg

def do_login(user):
    try:
        print(f"Attempting login for user: {user['email']}")
        res = brokers.stockbit.login.call(user['email'], user['password'])
        print(f"Login response received for {user['email']}")
        
        # Handle tuple response which indicates connection error
        if isinstance(res, tuple):
            error_msg = f"Connection error for {user['email']}: {res[1]}"
            print(error_msg)
            LOG.append(error_msg)
            return False, None
            
        if hasattr(res, 'status_code'):
            print(f"Response status code: {res.status_code}")
            if res.status_code == 200:
                security_token_status, security_token = get_security_token(user, res.json()['data']['access_token'])
                if security_token_status:
                    login_security_status, access_token_sekuritas = do_login_security(user, security_token)
                    if login_security_status:
                        print(f"Login security successful for user: {user['email']}")
                        return True, access_token_sekuritas
                    else:
                        print(f"Login security failed for user: {user['email']}")
                        msg = user["email"] + ": login security error"
                        LOG.append(msg)
                        return False, None
                else:
                    print(f"Security token error for user: {user['email']}")
                    msg = user["email"] + ": get security token error"
                    LOG.append(msg)
                    return False, None
            else:
                error_msg = f"Login failed for {user['email']} with status code {res.status_code}"
                print(error_msg)
                LOG.append(error_msg)
        else:
            error_msg = f"Unexpected response type for {user['email']}: {type(res)}"
            print(error_msg)
            LOG.append(error_msg)
            
        return False, None
    except Exception as e:
        error_msg = f"Login error for {user['email']}: {str(e)}"
        print(error_msg)
        LOG.append(error_msg)
        print(f"Exception type: {type(e)}")
        return False, None
    
def get_security_token(user, access_token):
    print(f"Attempting get security token for user: {user['email']}")
    res = brokers.stockbit.get_security_token.call(access_token)
    if res.status_code == 200:
        print(f"Security token received for user: {user['email']}")
        return True, res.json()['data']['token']
    else:
        return False, None
    
def do_login_security(user, security_token):
    print(f"Attempting login security for user: {user['email']}")
    res = brokers.stockbit.login_security.call(user, security_token)
    if res.status_code == 200:
        print(f"Login security successful for user: {user['email']}")
        return True, res.json()['data']['access_token']
    else:
        return False, None

def do_logout(access_token_sekuritas, user):
    print(f"Attempting logout for user: {user['email']}")
    res = brokers.stockbit.logout.call(access_token_sekuritas)
    if res.status_code == 200:
        print(f"Logout successful for user: {user['email']}")
        msg = user["email"] + ": logout OK"
        LOG.append(msg)
    else:
        msg = user["email"] + ": logout error: " + res.text
        print(msg)
        LOG.append(msg)

def get_signal_history():
    dir_path = get_dir_path()
    with open(f"{dir_path}\\signals\\history.csv", "r") as file:
        csvreader = csv.reader(file)
        if is_empty_csv(f"{dir_path}\\signals\\history.csv") == False:
            next(csvreader, None)
            list = []
            for row in csvreader:
                list.append([row['emiten'], row['signal_date'], row['buy_price'], row['take_profit'], row['cut_loss']])
        file.close()
    return list

def check_position(access_token_sekuritas, portofolio_dicts, user):
    print('Check position...')
    res = brokers.stockbit.order_list.call(access_token_sekuritas)
    if res.status_code == 200:
        data = res.json()
        order_list_dicts = data['data']

        for item in portofolio_dicts:
            emiten = item['symbol']
            lot = int(item['qty']['available']['lot'])
            dicts = [i for i in order_list_dicts if i['symbol'] == emiten]
            
            if len(dicts) == 2:
                print(emiten + ': Position ok')
            elif len(dicts) == 1:
                signal_history_dicts = [i for i in get_signal_history() if i[0] == emiten]
                
                for item in signal_history_dicts[-1]:
                    history_emiten = item[0]
                    history_take_profit = item[3]
                    history_cut_loss = item[4]
                    
                    if history_emiten == emiten:
                        smart_order_type = dicts[0]['smart_order']['label']
                        if smart_order_type == 'TP':
                            print('Re-create auto sell for take profit')
                            brokers.stockbit.sell.call(access_token_sekuritas, emiten, history_take_profit, lot, "TP")
                        else:
                            print('Re-create auto sell for cut loss')
                            brokers.stockbit.sell.call(access_token_sekuritas, emiten, history_cut_loss, lot, "SL")
            else:
                print('Remove unused auto trade setup')
                for order in order_list_dicts:
                    brokers.stockbit.cancel_smart_order.call(access_token_sekuritas, order['smart_order']['order_id'])
    else:
        msg = user["email"] + ": check position error: " + res.text
        LOG.append(msg)

def get_portfolio(access_token, user):
    print(f"Attempting get portfolio for user: {user['email']}")
    porto_res = brokers.stockbit.portfolio.call(access_token)
    if porto_res.status_code == 200:
        return porto_res.json()["data"]["results"]
    else:
        msg = user["email"] + ": get portfolio error: " + porto_res.text
        LOG.append(msg)

def position_size(access_token, user):
    print(f"Attempting get position size for user: {user['email']}")
    buying_power_res = brokers.stockbit.get_buying_power.call(access_token)
    if buying_power_res.status_code == 200:
        data_buying_power = buying_power_res.json()
        trading_limit = data_buying_power['data']['summary']['trading']['balance']
        amount = trading_limit / 5
        return amount
    else:
        msg = user["email"] + ": get position size error: " + buying_power_res.text
        LOG.append(msg)
        return 0

def buy(user, list_order):
    print(f"Attempting to buy for user: {user['email']}")
    LOG.append("Order Buy Report:")
    login_status, access_token = do_login(user)
    
    if login_status:
        amount = position_size(access_token, user)
        print(f"Amount: {amount}")

        for obj in list_order:
            lot = floor(( amount / float(obj.buy_price)) / 100)
            shares = lot * 100
            if lot < 1:
                print(f"Lot: {lot}")
                print(f"Shares: {shares}")
                print(f"Amount not enough for {obj.emiten}")
                msg = user["email"] + ": amount not enough"
                LOG.append(msg)
                return
            
            price = float(obj.buy_price) + (tick(float(obj.buy_price)) * 3)
            print(f"Price: {int(price)}")
        
            res = brokers.stockbit.buy.call(access_token, obj.emiten, int(price), int(shares))
            if res.status_code == 200:
                msg = user["email"] + ": order buy success: " + obj.emiten + " with id " + res.json()['data']['order_id']
                print(msg)
                LOG.append(msg)
                print(res.json())
            else:
                msg = user["email"] + ": order buy failed: " + obj.emiten + " error: " + res.text
                LOG.append(msg)
        
        # do_logout(access_token_sekuritas, user)
    else:
        msg = user["email"] + ": login failed when buy"
        LOG.append(msg)

def sell(user, list_order):
    print(f"Attempting to sell for user: {user['email']}")
    LOG.append("Order Sell Report:")
    LOG.append(f"Starting sell operation for user: {user['email']}")
    
    login_status, access_token = do_login(user)
    if login_status:
        LOG.append(f"Login successful for user: {user['email']}")
        portfolio = get_portfolio(access_token, user)
        if isinstance(portfolio, list) and portfolio != []:
            print(f"Portfolio retrieved successfully. Found {len(portfolio)} positions.")
            LOG.append(f"Portfolio retrieved successfully. Found {len(portfolio)} positions.")
            check_position(access_token, portfolio, user)

            for obj in list_order:
                emiten = obj.emiten
                take_profit = int(obj.take_profit)
                cut_loss = int(obj.cut_loss)
                
                msg = f"\nProcessing order for {emiten}:"
                msg += f"\n- Take Profit target: {take_profit}"
                msg += f"\n- Cut Loss target: {cut_loss}"
                LOG.append(msg)
                print(msg)
                
                dicts = [i for i in portfolio if i['symbol'] == emiten]
                
                if dicts != []:
                    position = dicts[0]
                    lot = position["qty"]["available"]["lot"]
                    shares = str(lot * 100)
                    current_price = position["price"]["latest"]
                    
                    msg = f"Position found for {emiten}:"
                    msg += f"\n- Available lots: {lot}"
                    msg += f"\n- Shares: {shares}"
                    msg += f"\n- Current price: {current_price}"
                    LOG.append(msg)
                    print(msg)
                    
                    msg = f"Attempting to set Take Profit order for {emiten}"
                    LOG.append(msg)
                    print(msg)
                    
                    res = brokers.stockbit.sell.call(access_token, emiten, take_profit, shares, "TP")
                    
                    if res.status_code == 200:
                        msg = f"{user['email']}: Take Profit order set for {emiten}"
                        msg += f"\n- Lots: {lot}"
                        msg += f"\n- Shares: {shares}"
                        msg += f"\n- TP Price: {take_profit}"

                        LOG.append(msg)
                        print(msg)
                        print(res.json())

                        time.sleep(3)
                        
                        LOG.append(f"Attempting to set Cut Loss order for {emiten}")
                        res = brokers.stockbit.sell.call(access_token, emiten, cut_loss, shares, "SL")
                        if res.status_code == 200:
                            msg = f"{user['email']}: Cut Loss order set for {emiten}"
                            msg += f"\n- Lots: {lot}"
                            msg += f"\n- Shares: {shares}"
                            msg += f"\n- CL Price: {cut_loss}"

                            LOG.append(msg)
                            print(msg)
                            print(res.json())
                        else:
                            msg = f"{user['email']}: Cut Loss order failed for {emiten}"
                            msg += f"\n- Error: {res.text}"
                            msg += f"\n- Status Code: {res.status_code}"
                            
                            print(msg)
                            LOG.append(msg)
                    else:
                        msg = f"{user['email']}: Take Profit order failed for {emiten}"
                        msg += f"\n- Error: {res.text}"
                        msg += f"\n- Status Code: {res.status_code}"
                        
                        print(msg)
                        LOG.append(msg)
                else:
                    msg = f"{user['email']}: Cannot setup sell orders for {emiten} - Position not found in portfolio"
                    print(msg)
                    LOG.append(msg)
        else:
            msg = f"{user['email']}: Portfolio is empty or could not be retrieved"
            print(msg)
            LOG.append(msg)
            
        print(f"Logging out user: {user['email']}")
        LOG.append(f"Logging out user: {user['email']}")
        do_logout(access_token, user)
    else:
        msg = f"{user['email']}: Login failed - Unable to proceed with sell orders"
        print(msg)
        LOG.append(msg)
    
def async_order(order_type, list_order, bot):
    print(f"Starting async_order with type: {order_type}")
    print(f"Number of orders to process: {len(list_order)}")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        print("Created thread pool executor")
        future_to_user = executor_submit(order_type, executor, list_order)
        print(f"Submitted {len(future_to_user)} tasks to executor")
        
        for future in concurrent.futures.as_completed(future_to_user):
            user = future_to_user[future]
            try:
                print(f"Processing result for user: {user['email']}")
                result = future.result()
                if result is None:
                    print(f"{user['email']}: RESULT OK")
                else:
                    print(f"{user['email']}: RESULT ERROR")
                    print(f"Error details: {result}")
                    _, _, tele_log_id = get_tele_data()
                    error_log(bot, tele_log_id)
            except Exception as e:
                print(f"Exception while processing future for {user['email']}: {str(e)}")
                _, _, tele_log_id = get_tele_data()
                error_log(bot, tele_log_id)

def executor_submit(order_type, executor, list_order):
    if order_type == "buy":
        return {executor.submit(buy, user, list_order): user for user in users.list}
    else:
        return {executor.submit(sell, user, list_order): user for user in users.list}

def tick(price):
    if price <= 200: 
        return 1
    elif price > 200 and price <= 500: 
        return 2
    elif price > 500 and price <= 2000: 
        return 5
    elif price > 2000 and price <= 5000: 
        return 10
    else: 
        return 25
    
def ara_hunter():
    [user] = users.list
    login_status, access_token = do_login(user)
    if login_status:
        for symbol in stocks.list:
            res = brokers.stockbit.orderbook.call(access_token, symbol)
            if res.status_code == 200:
                data = res.json()["data"]
                ara_raw = data["next_ara"]
                ara = int(ara_raw.replace(",", ""))
                lastprice = data["lastprice"]
                
                if lastprice == ara - (2*tick(ara)):
                    shares = 100
                    res = brokers.stockbit.buy.call(access_token, symbol, ara, shares)
                    if res.status_code == 200:
                        msg = user["email"] + ": order buy success: " + symbol + " with id " + res.json()['data']['order_id']
                        print(msg)
                        LOG.append(msg)
                        
                        
                    else:
                        msg = user["email"] + ": order buy failed: " + symbol + " error: " + res.text
                        LOG.append(msg)

async def send_telegram_message(bot, chat_id, message):
    await bot.send_message(chat_id=chat_id, text=message)

def send_log(bot, chat_id, log):
    print("Attempting to send log messages")
    print(f"Number of log messages: {len(log)}")
    try:
        message = join_msg(log)
        print(f"Combined message length: {len(message)}")
        # Split message if too long (Telegram has a 4096 character limit)
        max_length = 4000  # Leave some margin
        if len(message) > max_length:
            print("Message too long, splitting into chunks")
            chunks = [message[i:i+max_length] for i in range(0, len(message), max_length)]
            for i, chunk in enumerate(chunks):
                print(f"Sending chunk {i+1}/{len(chunks)}")
                asyncio.run(send_telegram_message(bot, chat_id, chunk))
        else:
            print("Sending single message")
            asyncio.run(send_telegram_message(bot, chat_id, message))
    except Exception as e:
        print(f"Error sending log: {str(e)}")
        print(f"Exception type: {type(e)}")

def join_msg(list):
    if list:
        return '\n'.join(list)
    else:
        return "Message is empty"

def send_msg_v2(bot, chat_ids, msg):
    for chat_id in chat_ids:
        bot.send_message(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN_V2)

def error_log(bot, chat_id):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    error_msg = traceback.format_exc()
    logger.debug(error_msg)
    asyncio.run(send_telegram_message(bot, chat_id, error_msg))
