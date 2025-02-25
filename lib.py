import brokers.ajaib.get_buying_power
import brokers.ajaib.login
import brokers.ajaib.logout
import brokers.ajaib.order
import brokers.ajaib.portfolio
import brokers.ajaib.auto_trading_list
import brokers.ajaib.delete_auto_trade
import brokers.ajaib.get_pin_data
import brokers.ajaib.validate_pin

import concurrent.futures
import csv
import telegram
import logging
import traceback
import os
import time
import users

from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

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
    # Login
    res = brokers.ajaib.login.call(user)
    if res.status_code == 200:
        data = res.json()
        pin_token = "jwt " + data["pin_token"]
        
        # Get pin data
        pin_res = brokers.ajaib.get_pin_data.call(pin_token)
        if pin_res.status_code == 200:
            # Validate pin
            validate_pin_res = brokers.ajaib.validate_pin.call(pin_token, user["pin"])
            if validate_pin_res.status_code == 200:
                access_token = "jwt " + validate_pin_res["result"]["access_token"]
            else:
                msg = user["email"] + ": validate pin error: " + validate_pin_res.text
                print(msg)
                LOG.append(msg)
                access_token = ""
        else:
            msg = user["email"] + ": get pin data error: " + pin_res.text
            print(msg)
            LOG.append(msg)
            access_token = ""
            
        msg = user["email"] + ": login OK"
        print(msg)
        LOG.append(msg)
        
        return validate_pin_res.status_code, access_token
    else:
        msg = user["email"] + ": login error: " + res.text
        LOG.append(msg)
        return res.status_code, data, ""

def do_logout(access_token, user):
    res = brokers.ajaib.logout.call(access_token)
    if res.status_code == 200:
        msg = user["email"] + ": logout OK"
        LOG.append(msg)
    else:
        msg = user["email"] + ": logout error: " + res.text
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

def check_position(access_token, porto_dicts, user):
    print('Check position...')
    res = brokers.ajaib.auto_trading_list.call(access_token)
    if res.status_code == 200:
        data = res.json()
        at_list_dicts = data["results"]

        for item in porto_dicts:
            emiten = item['stock']
            lot = int(item['lot'])
            dicts = [i for i in at_list_dicts if i['code'] == emiten]
            if len(dicts) == 2:
                print(emiten + ': Position ok')
            elif len(dicts) == 1:
                signal_history_dicts = [i for i in get_signal_history() if i[0] == emiten]
                for item in signal_history_dicts[-1]:
                    h_emiten = item[0]
                    h_tp = item[3]
                    h_cl = item[4]
                    if h_emiten == emiten:
                        comparator = dicts[0]['comparator']
                        if comparator == 'LTE':
                            print('Re-create auto sell for take profit')
                            brokers.ajaib.order.create_sell(access_token, emiten, h_tp, lot, "GTE")
                        else:
                            print('Re-create auto sell for cut loss')
                            brokers.ajaib.order.create_sell(access_token, emiten, h_cl, lot, "LTE")
            else:
                print('Remove unused auto trade setup')
                for trade in at_list_dicts:
                    brokers.ajaib.delete_auto_trade.call(access_token, trade['id'])
    else:
        msg = user["email"] + ": check position error: " + res.text
        LOG.append(msg)

def get_portfolio(access_token, user):
    porto_res = brokers.ajaib.portfolio.call(access_token)
    if porto_res.status_code == 200:
        porto_data = porto_res.json()
        return porto_data["result"]["portfolio"]
    else:
        msg = user["email"] + ": get portfolio error: " + porto_res.text
        LOG.append(msg)

def position_size(access_token, user):
    buying_power_res = brokers.ajaib.get_buying_power.call(access_token)
    if buying_power_res.status_code == 200:
        data_buying_power = buying_power_res.json()
        trading_limit = data_buying_power["result"]["trading_limit"]
        amount = trading_limit / 5
        return amount
    else:
        msg = user["email"] + ": get position size error: " + buying_power_res.text
        LOG.append(msg)
        return 0

def buy(user, list_order):
    LOG.append("Order Buy Report:")
    login_status, access_token = do_login(user)
    if login_status == 200:
        amount = position_size(access_token, user)

        for obj in list_order:
            res = brokers.ajaib.order.create_buy(access_token, obj.emiten, obj.buy_price, amount)
            if res.status_code == 200:
                msg = user["email"] + ": order buy " + obj.emiten + " sent"
                print(msg)
                LOG.append(msg)
                print(res.json())
            else:
                msg = user["email"] + ": order buy " + obj.emiten + " error: " + res.text
                LOG.append(msg)
        
        do_logout(access_token, user)
    else:
        msg = user["email"] + ": login error when buy"
        LOG.append(msg)

def sell(user, list_order):
    LOG.append("Order Sell Report:")
    login_status, access_token = do_login(user)
    if login_status == 200:
        portfolio = get_portfolio(access_token, user)
        if isinstance(portfolio, list) and portfolio != []:
            check_position(access_token, portfolio, user)

            for obj in list_order:
                emiten = obj.emiten
                tp = obj.take_profit
                cl = obj.cut_loss
                dicts = [i for i in portfolio if i['stock'] == emiten]
                
                if dicts != []:
                    lot = dicts[0]["lot"]
                    res = brokers.ajaib.order.create_sell(access_token, emiten, tp, lot, "GTE")
                    if res.status_code == 200:
                        msg = user["email"] + ": set TP " + emiten + " sent"
                        LOG.append(msg)
                        print(msg)
                        print(res.json())

                        time.sleep(3)

                        res = brokers.ajaib.order.create_sell(access_token, emiten, cl, lot, "LTE")
                        if res.status_code == 200:
                            msg = user["email"] + ": set CL " + emiten + " sent"
                            LOG.append(msg)
                            print(msg)
                            print(res.json())
                        else:
                            msg = user["email"] + ": set CL error: " + res.text
                            LOG.append(msg)
                    else:
                        msg = user["email"] + ": set TP error: " + res.text
                        LOG.append(msg)
                else:
                    LOG.append(user["email"] + ": setup sell " + emiten + " failed, not exists in portolio")
        else:
            msg = user["email"] + ": portfolio is empty"
            LOG.append(msg)
            
        do_logout(access_token, user)
    else:
        msg = user["email"] + ": login error when sell"
        LOG.append(msg)
    
def async_order(side, list_order, bot):
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = executor_submit(side, executor, list_order)
        for future in concurrent.futures.as_completed(future_to_user):
            user = future_to_user[future]
            try:
                if future.result() == None:
                    print(user["email"] + ": RESULT OK")
                else:
                    print(user["email"] + ": RESULT ERROR")
                    print(future.result())
            except Exception:
                _, tele_log_id = get_tele_data()
                error_log(bot, tele_log_id)

def executor_submit(side, executor, list_order):
    if side == "buy":
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

def send_log(bot, chat_id, log):
    bot.send_message(chat_id=chat_id, text=join_msg(log))

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
    bot.send_message(chat_id=chat_id, text=error_msg)
