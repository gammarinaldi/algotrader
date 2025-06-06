import csv
import time
import lib
import os
import requests
from datetime import datetime

def is_holiday():
    """
    Check if today is a holiday using the holiday API.
    
    Returns:
        bool: True if today is a holiday, False otherwise
    """
    try:
        today = datetime.now()
        month = today.month
        year = today.year
        
        # Call holiday API
        response = requests.get(f"https://api-harilibur.vercel.app/api?month={month}&year={year}")
        if response.status_code == 200:
            holidays = response.json()
            today_str = today.strftime("%Y-%m-%d")
            
            # Check if today is in the holiday list
            for holiday in holidays:
                if holiday["holiday_date"] == today_str and holiday["is_national_holiday"]:
                    print(f"Today is a holiday: {holiday['holiday_name']}")
                    return True
        return False
    except Exception as e:
        print(f"Error checking holiday: {str(e)}")
        return False

if __name__ == '__main__':
    print("Algotrader is starting...")

    # Check if today is a holiday
    if is_holiday():
        print("Today is a holiday. Skipping trading process.")
        exit()

    bot, tele_chat_ids, tele_log_id = lib.get_tele_bot()
    enable_signal, enable_buy, enable_sell, sell_delay, dir_path = lib.get_env()
    print(f"Working directory: {dir_path}")

    try:
        # Use os.path.join for cross-platform path handling
        signals_dir = os.path.join(dir_path, "signals")
        os.makedirs(signals_dir, exist_ok=True)
        
        result = lib.get_result()
        
        if isinstance(result, str):
            print(result)
        else:
            list_order = []
            for row in result:
                emiten = row[0]
                signal_date = row[1]
                buy_price = row[2]
                take_profit = row[3]
                cut_loss = row[4]

                # Save signal history
                with open(f"{dir_path}\\signals\\history.csv", 'a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file) #this is the writer object
                    writer.writerow([emiten, signal_date, buy_price, take_profit, cut_loss]) #this is the data
                    file.close()                

                msg = "💌 Rekomendasi Algo Trader (" + signal_date + ")\n\n*Buy $" + emiten + "\nBuy @" + buy_price + "\nTake Profit @" + take_profit + "\nCutloss @" + cut_loss + "*\n\n_Disclaimer ON. DYOR._"
                print(msg)

                # Send signal to telegram
                if enable_signal == "TRUE":
                    if not lib.send_msg_v2(bot, tele_chat_ids, msg):
                        print("Failed to send signal to Telegram")

                # Input order parameters for auto order
                list_order.append(lib.data_order(emiten, signal_date, buy_price, take_profit, cut_loss))

            # Perform auto order buy
            if enable_buy == "TRUE":
                try:
                    t1 = time.time()
                    lib.async_order("buy", list_order, bot)
                    t2 = time.time()
                    diff = t2 - t1
                    print("Processing auto-buy order takes: " + str(round(diff, 2)) + " secs.")
                    
                    # Send logs in a single call
                    if lib.LOG:
                        if not lib.send_log(bot, tele_log_id, lib.LOG):
                            print("Failed to send buy order logs to Telegram")
                        lib.LOG = []
                except Exception as e:
                    print(f"Error during buy order: {e}")
                    if not lib.error_log(bot, tele_log_id):
                        print("Failed to send error log to Telegram")

            # Perform auto order sell
            if enable_sell == "TRUE":
                print('Wait 1 hour to create auto sell order')
                time.sleep(int(sell_delay))

                t1 = time.time()

                # Async sell
                lib.async_order("sell", list_order, bot)

                t2 = time.time()
                diff = t2 -t1
                
                print("Processing auto-sell order takes: " + str(round(diff, 2)) + " secs.")
                if lib.LOG:
                    if not lib.send_log(bot, tele_log_id, lib.LOG):
                        print("Failed to send sell order logs to Telegram")
                    lib.LOG = []
    except Exception as error:
        print(error)
        if not lib.error_log(bot, tele_log_id):
            print("Failed to send error log to Telegram")

    print("Done.")

