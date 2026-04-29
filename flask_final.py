__author__ = 'WizzardTim'
from flask import Flask
from flask import render_template,jsonify
from flask import request, redirect, url_for
import logging as Logger
import restructured as pnfengine, API_poloniex as polo, fileFunctions as f
import datetime
import os
import pandas as pd
import gc
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import time
import ccxt

app = Flask(__name__)
LIVE_MARKET_CACHE = {
    "exchange": "mexc",
    "updated_at": None,
    "symbols": {}
}


def resolve_exchange_id(selected_exchange):
    """
    Resolve exchange aliases so UI names remain stable across ccxt versions.
    """
    if selected_exchange == "mexc" and "mexc" not in ccxt.exchanges and "mexc3" in ccxt.exchanges:
        return "mexc3"
    if selected_exchange == "mexc3" and "mexc3" not in ccxt.exchanges and "mexc" in ccxt.exchanges:
        return "mexc"
    return selected_exchange


def create_exchange_instance(selected_exchange):
    """
    Build ccxt exchange instance with safe defaults for market data pulls.
    """
    exchange_id = resolve_exchange_id(selected_exchange)
    if exchange_id not in ccxt.exchanges:
        return None

    exchange_class = getattr(ccxt, '%s' % exchange_id)
    return exchange_class({
        'enableRateLimit': True,
        'timeout': 20000,
    })


def get_live_symbols():
    raw_symbols = os.getenv("LIVE_MEXC_SYMBOLS", "BTC/USDT,ETH/USDT")
    return [s.strip() for s in raw_symbols.split(",") if s.strip()]


def update_mexc_live_snapshot():
    exchange = create_exchange_instance("mexc")
    if exchange is None:
        exchange = create_exchange_instance("mexc3")
    if exchange is None:
        return

    symbols = get_live_symbols()
    snapshot = {}
    for symbol in symbols:
        try:
            ticker = exchange.fetch_ticker(symbol)
            snapshot[symbol] = {
                "last": ticker.get("last"),
                "bid": ticker.get("bid"),
                "ask": ticker.get("ask"),
                "timestamp": ticker.get("timestamp")
            }
        except:
            continue

    if len(snapshot) > 0:
        LIVE_MARKET_CACHE["exchange"] = exchange.id
        LIVE_MARKET_CACHE["updated_at"] = int(time.time())
        LIVE_MARKET_CACHE["symbols"] = snapshot

# Scheduler cron-style
cron = BackgroundScheduler(daemon=True)

# Explicitly kick off the background thread
cron.start()

# Update Poloniex active currencies every 3 days
#@cron.interval_schedule(days=3)  # start_date='define correct UTC hour' or timezone=utc
def update_active_currencies():
    # Change global variable
    global active_currencies

    # Fetch active currencies list
    active_currencies = polo.poloniex().get_poloniex_active_currencies()


# We can also set start_date='2013-08-06 00:09:12' in add_interval)job
# so that it runs on correct UTC as polo does
#@cron.interval_schedule(days=1,timezone=utc)  # start_date='define correct UTC hour'
def job_fetch_polo_data_1d():

    # 1. Create specific directory for 1 day if it does not exist yet
    # 2. Fetch Poloniex .json 1 day data using UTC time

    print("Cron: starting fetching daily data from Poloniex")

    # 1
    dirname = 'poloniex_output_1d'
    f.create_dir(dirname)

    # 2
    # Get JSON data from Poloniex, based on what the user entered
    # from form data data_period = 86400 / 14400 etc
    # from form data zoom = all / 1m / 2w / 2h etc

    # data_period is daily -> 86400
    time_period = 86400
    from_timestamp = 'All'

    for currency in active_currencies:
        # zoom not needed now, so for all these cron jobs, it would be 'all'
        polo.poloniex().update_specific_historical_data_to_json(currency=currency, data_period=time_period, from_timestamp=from_timestamp,
                                                                dirname=dirname)



#@cron.interval_schedule(hours=4)
def job_fetch_polo_data_4h():
    # 1. Create specific directory for 4h if it does not exist yet
    # 2. Fetch Poloniex .json 4h data using UTC time

    print("Cron: starting fetching 4h data from Poloniex")

    # 1
    dirname = 'poloniex_output_4h'
    f.create_dir(dirname)


    # 2
    # Get JSON data from Poloniex, based on what the user entered
    # from form data data_period = 86400 / 14400 etc
    # from form data zoom = all / 1m / 2w / 2h etc

    # data_period is daily -> 86400
    time_period = 14400
    from_timestamp = '2w'

    for currency in active_currencies:
        # zoom not needed now, so for all these cron jobs, it would be 'all'
        polo.poloniex().update_specific_historical_data_to_json(currency=currency, data_period=time_period, from_timestamp=from_timestamp,
                                                                dirname=dirname)


#@cron.interval_schedule(hours=2)
def job_fetch_polo_data_2h():
    # 1. Create specific directory for 2h if it does not exist yet
    # 2. Fetch Poloniex .json 2h data using UTC time

    print("Cron: starting fetching 2h data from Poloniex")

    # 1
    dirname = 'poloniex_output_2h'
    f.create_dir(dirname)


    # 2
    # Get JSON data from Poloniex, based on what the user entered
    # from form data data_period = 86400 / 14400 etc
    # from form data zoom = all / 1m / 2w / 2h etc

    # data_period is daily -> 86400
    time_period = 7200
    from_timestamp = '1w'

    for currency in active_currencies:
        # zoom not needed now, so for all these cron jobs, it would be 'all'
        polo.poloniex().update_specific_historical_data_to_json(currency=currency, data_period=time_period, from_timestamp=from_timestamp,
                                                                dirname=dirname)


#@cron.interval_schedule(minutes=30)
def job_fetch_polo_data_30m():
    # 1. Create specific directory for 30m if it does not exist yet
    # 2. Fetch Poloniex .json 30m data using UTC time


    print("Cron: starting fetching 30m data from Poloniex")

    # 1
    dirname = 'poloniex_output_30m'
    f.create_dir(dirname)


    # 2
    # Get JSON data from Poloniex, based on what the user entered
    # from form data data_period = 86400 / 14400 etc
    # from form data zoom = all / 1m / 2w / 2h etc

    # data_period is daily -> 86400
    time_period = 1800
    from_timestamp = '1w'

    for currency in active_currencies:
        # zoom not needed now, so for all these cron jobs, it would be 'all'
        polo.poloniex().update_specific_historical_data_to_json(currency=currency, data_period=time_period, from_timestamp=from_timestamp,
                                                                dirname=dirname)


#@cron.interval_schedule(minutes=15)
def job_fetch_polo_data_15m():
    # 1. Create specific directory for 15m if it does not exist yet
    # 2. Fetch Poloniex .json 15m data using UTC time


    print("Cron: starting fetching 15m data from Poloniex")

    # 1
    dirname = 'poloniex_output_15m'
    f.create_dir(dirname)


    # 2
    # Get JSON data from Poloniex, based on what the user entered
    # from form data data_period = 86400 / 14400 etc
    # from form data zoom = all / 1m / 2w / 2h etc

    # data_period is daily -> 86400
    time_period = 900
    from_timestamp = '4d'

    for currency in active_currencies:
        # zoom not needed now, so for all these cron jobs, it would be 'all'
        polo.poloniex().update_specific_historical_data_to_json(currency=currency, data_period=time_period, from_timestamp=from_timestamp,
                                                                dirname=dirname)




# Convert current time to UTC timezone
utc_datetime = datetime.datetime.utcnow()

# Set time to start on todays start (00:00:00) expressed in UTC
today_utc_start = utc_datetime.strftime("%Y-%m-%d")+" 00:00:00"

# Add functions to scheduler
cron.add_job(update_active_currencies, 'interval', days=1, start_date=today_utc_start)#
cron.add_job(update_mexc_live_snapshot, 'interval', seconds=10)
#cron.add_job(job_fetch_polo_data_1d, 'interval', days=1, start_date=today_utc_start)
#cron.add_job(job_fetch_polo_data_4h, 'interval', hours=4, start_date=today_utc_start)
#cron.add_job(job_fetch_polo_data_2h, 'interval', hours=2, start_date=today_utc_start)
#cron.add_job(job_fetch_polo_data_30m, 'interval', minutes=30, start_date=today_utc_start)
#cron.add_job(job_fetch_polo_data_15m, 'interval', minutes=15, start_date=today_utc_start)

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))


@app.route('/')
def main_page():
    selectedParams = {
        'pair': 'BTC/USD',
        'period': '',
        'boxsize': '',
        'reversal': '',
        'type': '',
        'zoom': ''
    }

    # Render template with active currencies droplist in selectbox
    default_exchange = 'mexc' if 'mexc' in ccxt.exchanges else ('mexc3' if 'mexc3' in ccxt.exchanges else 'kraken')
    return render_template('container_template_updated.html',exchanges = ccxt.exchanges,
                           default = default_exchange,defaultParams = selectedParams )


@app.route('/home')
def home():
    return redirect(url_for('main_page'))


@app.route("/live/mexc", methods=['GET'])
def get_mexc_live_snapshot():
    return jsonify(LIVE_MARKET_CACHE)

@app.route("/getInfo/<selectedExchange>", methods=['GET'])
def getInfo(selectedExchange):
    if(selectedExchange == "undefined"):
        selectedExchange = "_1btcxe"
    selectedExchange = resolve_exchange_id(selectedExchange)

    response = {"msg" : "error"}
    exchange = create_exchange_instance(selectedExchange)
    if exchange is not None:
        try:
            times = exchange.timeframes
            markets = exchange.fetch_markets()

            pairs = []
            for market in markets:
                pairs.append(market['symbol'])
            pairs.sort()

            response = {
                "timeFrames": times,
                "pairs":     pairs
            }
        except:
            response = {"msg": "error"}

    return jsonify(response)

@app.route('/draw_chart',methods=['POST'])
def draw_chart():

    # Explicit call to Garbage Collector - free up memory
    gc.collect()

    print("Got user input fields - start processing data.")

    #  TODO loading Screen - check http://stackoverflow.com/questions/14525029/display-a-loading-message-while-a-time-consuming-function-is-executed-in-flask

    # Get input data from form
    selectedExchange = resolve_exchange_id(request.form['Exchange'].lower())
    if selectedExchange not in ccxt.exchanges:
        return redirect(url_for('main_page'))

    currency_pair = request.form['Currency_Pair'] # BTC_EXP etc
    time_period = request.form['Time_Period'] # 'Daily', '4hr', '2hr'
    boxsize = request.form['Boxsize'] # 1%, 2%, 3% or Arithmetic Scale e.g. 1,2,5,10 Satoshi
    reversal = int(request.form['Reversal']) # 1-5
    pnf_type = request.form['Type'] # 'Close' or 'High/Low'
    zoom = request.form['Zoom']  # Zoom period e.g. 1 month
    time_period_string = str(time_period)

    selectedParams = {
        'pair' :    currency_pair,
        'period':   time_period,
        'boxsize' : boxsize,
        'reversal': reversal,
        'type' :    pnf_type,
        'zoom' :    zoom
    }

    if zoom == "All":
        since = None
    elif zoom == "3m":
        since = int(time.time()) - 7776000
    elif zoom == "2m":
        since = int(time.time()) - 5184000
    elif zoom == "1m":
        since = int(time.time()) - 2592000
    elif zoom == "2w":
        since = int(time.time()) - 1209600
    elif zoom == "1w":
        since = int(time.time()) - 604800
    elif zoom == "4d":
        since = int(time.time()) - 345600
    elif zoom == "2d":
        since = int(time.time()) - 172800
    elif zoom == "1d":
        since = int(time.time()) - 86400
    elif zoom == "8h":
        since = int(time.time()) - 28800
    elif zoom == "6h":
        since = int(time.time()) - 21600
    elif zoom == "2h":
        since = int(time.time()) - 7200
    elif zoom == "1h":
        since = int(time.time()) - 3600

    tmp_folder = "tmp"

    if f.is_dir_exist(tmp_folder) == False:
        f.create_dir(tmp_folder)

    json_filename_to_fetch = tmp_folder+"\\"+selectedExchange+currency_pair.replace("/","_")+time_period+"_"+str(since)+"_"+str(int(time.time()))+".json"

    exchange = create_exchange_instance(selectedExchange)
    if exchange is None:
        return redirect(url_for('main_page'))

    try:
        response = exchange.fetch_ohlcv(currency_pair,time_period,since)
    except:
        return redirect(url_for('main_page'))

    # response = response[-20::]
    results = []

    for row in response:
        results.append({
            "date" : row[0],
            "high" : row[2],
            "low"  : row[3],
            "close": row[4]
        })

    totalHistoricalDataFetched = len(results)

    f.file_save_json_contents(json_filename_to_fetch,results);

    # Feed the .json into appropriate PnF engine, with the submitted form parameters, in order to create the svg
    # We will use 2 services from the engine - the main PnF Close/High_Low engine
    pnfengine.set_pandas_and_numpy_options("cryptocoins")

    try:
        #MyPandasFrame = pd.read_json(path_or_buf = 'poloniex_output'+f.PATH_SEPARATOR+currency_pair+".json",
        #                             orient = 'DataFrame',
        #                             precise_float = True)
        MyPandasFrame = pd.read_json(path_or_buf = json_filename_to_fetch,
                                     orient = 'DataFrame',
                                     precise_float=True)
        f.file_delete(json_filename_to_fetch)
    except:
        return redirect(url_for('main_page'))

    # Add zoom function to .json and keep only the needed lines
    # if time_period_string == 'Daily':
    #     if zoom == 'All':  # keep all rows
    #         MyPandasFrame = MyPandasFrame.tail(100);
    #         index = range(0,len(MyPandasFrame),1);
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     if zoom == '1m':  # keep last 30 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(30)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '2w':  # keep last 14 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(14)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '1w':  # keep last 7 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(7)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    # elif time_period_string == '4-hr':
    #     # one day has 6*4h
    #     if zoom == '2w':  # keep last 84 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(84)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '1w':  # keep last 42 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(42)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '4d':  # keep last 24 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(24)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '2d':  # keep last 12 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(12)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '1d':  # keep last 6 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(6)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    # elif time_period_string == '2-hr':
    #     # one day has 12*2h
    #     if zoom == '1w':  # keep last 84 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(84)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '4d':  # keep last 48 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(48)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '2d':  # keep last 24 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(24)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '1d':  # keep last 12 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(12)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    # elif time_period_string == '30-min':
    #
    #     # one day has 48*30m
    #     if zoom == '1w':  # keep last 336 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(336)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '4d':  # keep last 192 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(192)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '2d':  # keep last 96 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(96)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '1d':  # keep last 48 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(48)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '8h':  # keep last 16 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(16)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    # elif time_period_string == '15-min':
    #
    #     # one day has 96*15m
    #     if zoom == '4d':  # keep last 384 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(384)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '2d':  # keep last 192 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(192)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '1d':  # keep last 96 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(96)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '8h':  # keep last 32 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(32)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])
    #
    #     elif zoom == '6h':  # keep last 24 rows & set index correctly starting from zero
    #         MyPandasFrame = MyPandasFrame.tail(24)
    #         index = range(0,len(MyPandasFrame),1)
    #         MyPandasFrame = MyPandasFrame.set_index([index])


    # Enable this if you want to check initial .json data into human readable html format
    #MyPandasFrame.to_html(open(current_filename+'unprocessed_Df.html','w'))

    #  TIP (Boxsize):
    # Having one of the following values:
    # 1% 0.009950331
    # 2% 0.019802627
    # 3% 0.029558802

    #                 1%           2%           3%
    # boxsize = [0.009950331, 0.019802627, 0.029558802]
    if boxsize == '1p':
        box = 0.009950331
        box_string = "1 percent"
        log = True
    elif boxsize == '2p':
        box = 0.019802627
        box_string = "2 percent"
        log = True
    elif boxsize == '3p':
        box = 0.029558802
        box_string = "3 percent"
        log = True
    elif boxsize == '1':
        box = 0.00000001
        box_string = "1 Satoshi"
        log = False
    elif boxsize == '2':
        box = 0.00000002
        box_string = "2 Satoshi"
        log = False
    elif boxsize == '5':
        box = 0.00000005
        box_string = "5 Satoshi"
        log = False
    elif boxsize == '10':
        box = 0.00000010
        box_string = "10 Satoshi"
        log = False
    elif boxsize == '20':
        box = 0.00000020
        box_string = "20 Satoshi"
        log = False
    elif boxsize == '25':
        box = 0.00000025
        box_string = "25 Satoshi"
        log = False
    elif boxsize == '100':
        box = 0.00000100
        box_string = "100 Satoshi"
        log = False
    elif boxsize == '150':
        box = 0.00000150
        box_string = "150 Satoshi"
        log = False
    elif boxsize == '200':
        box = 0.00000200
        box_string = "200 Satoshi"
        log = False
    elif boxsize == '250':
        box = 0.00000250
        box_string = "250 Satoshi"
        log = False
    elif boxsize == '500':
        box = 0.00000500
        box_string = "500 Satoshi"
        log = False
    elif boxsize == '1000':
        box = 0.00001000
        box_string = "1000 Satoshi"
        log = False
    elif boxsize == '2000':
        box = 0.00002000
        box_string = "2000 Satoshi"
        log = False
    elif boxsize == '5000':
        box = 0.00005000
        box_string = "5000 Satoshi"
        log = False
    elif boxsize == '10000':
        box = 0.00010000
        box_string = "10000 Satoshi"
        log = False
    elif boxsize == '20000':
        box = 0.00020000
        box_string = "20000 Satoshi"
        log = False
    elif boxsize == '25000':
        box = 0.00025000
        box_string = "25000 Satoshi"
        log = False
    elif boxsize == '50000':
        box = 0.00050000
        box_string = "50000 Satoshi"
        log = False

    # Initialization of parameters
    dwg=""
    dwg2=""
    chart_svg = ""
    chart_text = ""
    scale_svg = ""
    result_df_PnF = ""

    # Construct chart based on type of chart
    if pnf_type == 'Close':
        # Call Main PnF Engine using Close
        result_df_PnF = pnfengine.main_pnf_engine_using_close_data(MyPandasFrame, boxsize=box, reversal=reversal, log=log)

        # If result is string - then an exception is caught - either due to large PnF or wrong parameters, e.g. Boxsize
        if type(result_df_PnF)==str:

            if result_df_PnF == "exception-columns more than 2000":

                chart_svg = "<img src=""static/forever.jpg"" style=""float:left;margin-top:50px;padding-right:50px;"">" \
                            "<br><br><h4><small>Generated chart has more than 2000 Columns! " \
                            "<br><br>Please try with a bigger <mark>Boxsize</mark> or <mark>Reversal</mark>.<br>" \
                            "<br>E.g. you can try selecting a Boxsize with percentage (Log Scale)." \
                            "<br><br><mark>Smaller Zoom</mark> also helps!</small> </h4>"

                chart_text = selectedExchange+": "+str(currency_pair)+" "+time_period_string+" Close PnF Chart: "+box_string+" boxsize - "+str(reversal)+" box reversal - zoom: "+str(zoom)+" Total Historic Samples Fetched:"+str(totalHistoricalDataFetched)

            elif result_df_PnF == "exception-small boxsize entered": # wrong boxsize - PnF cannot be calculated at all

                chart_svg = "<img src=""static/boxsize.jpg"" style=""float:left;margin-top:50px;padding-right:50px;"  ">" \
                            "<br><br><h4><small>Oops!! Please try with an appropriate" \
                            "<mark> Boxsize.</mark> <br><br>That was too small or too big for this asset!</small></h4>"

                chart_text = selectedExchange+": "+str(currency_pair)+" "+time_period_string+" Close PnF Chart: "+box_string+" boxsize - "+str(reversal)+" box reversal - zoom: "+str(zoom)+" Total Historic Samples Fetched:"+str(totalHistoricalDataFetched)

            elif result_df_PnF == "exception-height more than 1000":

                chart_svg = "<img src=""static/forever.jpg"" style=""float:left;margin-top:50px;padding-right:50px;"">" \
                            "<br><br><h4><small>Generated chart has more than 1000 Boxes height! " \
                            "<br><br>Please try with a bigger <mark>Boxsize</mark> or <mark>Reversal</mark>.<br>" \
                            "<br>E.g. you can try selecting a Boxsize with percentage (Log Scale)." \
                            "<br><br><mark>Smaller Zoom</mark> also helps!</small> </h4>"

                chart_text = selectedExchange+": "+str(currency_pair)+" "+time_period_string+" Close PnF Chart: "+box_string+" boxsize - "+str(reversal)+" box reversal - zoom: "+str(zoom)+" Total Historic Samples Fetched:"+str(totalHistoricalDataFetched)


        else: # Result is a PnF dataframe

            # Call Charting Engine using Close
            dwg_filename, dwg2_filename = pnfengine.charting_engine(result_df_PnF,filename=selectedExchange+currency_pair.replace("/","_")+str(since)+zoom, highlow_close="close", boxsize=box, reversal=reversal, log=log)

            #scale_svg = dwg2.tostring()
            #chart_svg = dwg.tostring()
            chart_text = selectedExchange+": "+str(currency_pair)+" "+time_period_string+" Close PnF Chart: "+box_string+" boxsize - "+str(reversal)+" box reversal - zoom: "+str(zoom)+" Total Historic Samples Fetched:"+str(totalHistoricalDataFetched)

            try:
                print(("Trying to read file:"+dwg2_filename))
                scale_svg = open(dwg2_filename, 'r').read()
                print(("Trying to read file:"+dwg_filename))
                chart_svg = open(dwg_filename, 'r').read()
            except:
                print("exception while trying to read SVGs")
                return redirect(url_for('main_page'))


    elif pnf_type == 'High/Low':

        # Call Main PnF Engine using High & Low data
        result_df_PnF = pnfengine.main_pnf_engine_using_high_low_data(MyPandasFrame, boxsize=box, reversal=reversal, log=log)

        if type(result_df_PnF)==str:

            if result_df_PnF == "exception-columns more than 2000":

                chart_svg = "<img src=""static/forever.jpg"" style=""float:left;margin-top:50px;padding-right:50px;"">" \
                            "<br><br><h4><small>Generated chart has more than 2000 Columns! " \
                            "<br><br>Please try with a bigger <mark>Boxsize</mark> or <mark>Reversal</mark>.<br>" \
                            "<br>E.g. you can try selecting a Boxsize with percentage (Log Scale)." \
                            "<br><br><mark>Smaller Zoom</mark> also helps!</small> </h4>"

                chart_text = selectedExchange+": "+str(currency_pair)+" "+time_period_string+" High/Low PnF Chart: "+box_string+" boxsize - "+str(reversal)+" box reversal - zoom: "+str(zoom)+" Total Historic Samples Fetched:"+str(totalHistoricalDataFetched)


            elif result_df_PnF == "exception-small boxsize entered": # wrong boxsize - PnF cannot be calculated at all

                chart_svg = "<img src=""static/boxsize.jpg"" style=""float:left;margin-top:50px;padding-right:50px;"  ">" \
                            "<br><br><h4><small>Oops!! Please try with an appropriate" \
                            "<mark> Boxsize.</mark> <br><br>That was too small or too big for this asset!</small></h4>"

                chart_text = selectedExchange+": "+str(currency_pair)+" "+time_period_string+" High/Low PnF Chart: "+box_string+" boxsize - "+str(reversal)+" box reversal - zoom: "+str(zoom)+" Total Historic Samples Fetched:"+str(totalHistoricalDataFetched)

            elif result_df_PnF == "exception-height more than 1000":

                chart_svg = "<img src=""static/forever.jpg"" style=""float:left;margin-top:50px;padding-right:50px;"">" \
                            "<br><br><h4><small>Generated chart has more than 1000 Boxes height! " \
                            "<br><br>Please try with a bigger <mark>Boxsize</mark> or <mark>Reversal</mark>.<br>" \
                            "<br>E.g. you can try selecting a Boxsize with percentage (Log Scale)." \
                            "<br><br><mark>Smaller Zoom</mark> also helps!</small> </h4>"

                chart_text = selectedExchange+": "+str(currency_pair)+" "+time_period_string+" High/Low PnF Chart: "+box_string+" boxsize - "+str(reversal)+" box reversal - zoom: "+str(zoom)+" Total Historic Samples Fetched:"+str(totalHistoricalDataFetched)


        else:

            # Call Charting Engine using High & Low data
            #dwg, dwg2 = pnfengine.charting_engine(result_df_PnF,filename=currency_pair, highlow_close="high_low", boxsize=box, reversal=reversal, log=log)
            dwg_filename, dwg2_filename = pnfengine.charting_engine(result_df_PnF,filename=selectedExchange+currency_pair.replace("/","_")+str(since)+zoom, highlow_close="high_low", boxsize=box, reversal=reversal, log=log)

            chart_text = selectedExchange+": "+str(currency_pair)+" "+time_period_string+" High/Low PnF Chart: "+box_string+" boxsize - "+str(reversal)+" box reversal - zoom: "+str(zoom)+" Total Historic Samples Fetched:"+str(totalHistoricalDataFetched)
            #scale_svg = dwg2.tostring()
            #chart_svg = dwg.tostring()
            try:
                print(("Trying to read file:"+dwg2_filename))
                scale_svg = open(dwg2_filename, 'r').read()
                print(("Trying to read file:"+dwg_filename))
                chart_svg = open(dwg_filename, 'r').read()
            except:
                print("exception while trying to read SVGs")
                return redirect(url_for('main_page'))


    # Now these charts are stored to memory, no more disk I/O
    # Correct xml representation - avoiding disk I/O
    print(("pair selected", currency_pair))

    # Script to preserve currency pair value
    js_script = "$(\'select[name=\"Currency_Pair\"] option[value=\""+currency_pair+"\"]\').attr(\"selected\",true);"



    return render_template("container_template_updated.html", scale_svg=scale_svg, chart_svg=chart_svg,
                             chart_text=chart_text, js_script=js_script,exchanges = ccxt.exchanges,
                             default = selectedExchange,defaultParams = selectedParams)

    # Old way, when using disk-stored SVG files instead of stored-to RAM
    #return render_template("container_template.html", scale_svg=open(scale_svg).read(), chart_svg=open(chart_svg).read(),
    #                       active_currencies=active_currencies, chart_text=chart_text)






if __name__ == '__main__':
    #app.run(host='0.0.0.0') # Replace IP with public one for external connections

    # Start logger with INFO output level
    Logger.basicConfig(level=Logger.INFO)

    # Get active currencies list
    print("Fetching current active currencies in Poloniex:")

    # This will be used as global
    active_currencies = polo.poloniex().get_poloniex_active_currencies()

    # Populate .json - run once
    #job_fetch_polo_data_1d()
    #job_fetch_polo_data_4h()
    #job_fetch_polo_data_2h()
    #job_fetch_polo_data_30m()
    #job_fetch_polo_data_15m()

    # Start Web App
    app.run(debug=False, threaded=True)
    # app.run(debug=True, threaded=True)
