import csv
import time
import lib
import os
# import gsheet.process

if __name__ == '__main__':
    print("Algotrader is starting...")

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
            # Export signal to google sheet
            # gsheet.process.write(result)
            
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
                    lib.send_msg_v2(bot, tele_chat_ids, msg)

                # Input order parameters for auto order
                list_order.append(lib.data_order(emiten, buy_price, take_profit, cut_loss))

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
                        lib.send_log(bot, tele_log_id, lib.LOG)
                        lib.LOG = []
                except Exception as e:
                    print(f"Error during buy order: {e}")
                    lib.error_log(bot, tele_log_id)

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
                lib.send_log(bot, tele_log_id, lib.LOG)
                lib.LOG = []
    except Exception as error:
        print(error)
        lib.error_log(bot, tele_log_id)

    print("Done.")

