import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import json
import time
import hmac,hashlib
import fileFunctions as f
import os
from datetime import datetime
#import xlsxwriter
import logging as Logger
import re

# Add datetime library (6/5/2015 - Efthimis)
# Begin
from datetime import date, timedelta
# End

Logger.basicConfig(level=Logger.INFO)

if __name__ == '__main__':
    exit(1)

def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))

class poloniex:
    def __init__(self, APIKey, Secret, time_out=180):
        self.APIKey = APIKey
        self.Secret = Secret
        self.socket_timeout = time_out
   
    def __init__(self, time_out=180):
        self.socket_timeout = time_out

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if('return' in after):
            if(isinstance(after['return'], list)):
                for x in range(0, len(after['return'])):
                    if(isinstance(after['return'][x], dict)):
                        if('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
                            after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))
                            
        return after

    def api_query(self, command, req={}):
        """
        Takes as input the Poloniex REST API command and any extra arguments in a dictionary and returns
        the results as json data
        :param command: Poloniex REST API command as string
        :param req: Extra command arguments as a dictionary
        :return: json data
        """
        try:
            if(command == "returnTicker" or command == "return24hVolume"):
                ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=' + command), timeout = self.socket_timeout)
                return json.loads(ret.read())
            elif(command == "returnOrderBook"):
                ret = urllib.request.urlopen(urllib.request.Request('http://poloniex.com/public?command=' + command + '&currencyPair=' + str(req['currencyPair'])), timeout = self.socket_timeout)
                return json.loads(ret.read())
            # Add API call for Candlestick Chart Data (4/5/2015 - Efthimis)
            # Begin
            elif(command == "returnChartData"): # get last day ONLY
                # get yesterday's date:
                yesterday = date.today() - timedelta(days=1)
                 # get today's date:
                #today = str(time.strftime("%Y-%m-%d"))
                today = date.today()
                # print the command before the request
                print(('https://poloniex.com/public?command=returnChartData&currencyPair=' + str(req['currencyPair']) + '&start=' + str(createTimeStamp(str(yesterday) + " 16:00:00")) + '&end=' + str(createTimeStamp(str(today) + " 16:00:00")) + '&period=14400'))
                ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=returnChartData&currencyPair=' + str(req['currencyPair']) + '&start=' + str(createTimeStamp(str(yesterday) + " 16:00:00")) + '&end=' + str(createTimeStamp(str(today) + " 16:00:00")) + '&period=14400'), timeout = self.socket_timeout)
                return json.loads(ret.read())
            elif(command == "returnFullChartData"): # get everything till last day - this will run only once, to get the initial json objects with all historical data
                # get today's date:
                #today = str(time.strftime("%Y-%m-%d"))
                from_timestamp = createTimeStamp("2012-01-01 16:00:00")
                to_timestamp = createTimeStamp(str(date.today()) + " 16:00:00")
                try:
                    if req['from_timestamp']:
                        from_timestamp = req['from_timestamp']
                except:
                    pass

                try:
                    if req['to_timestamp']:
                        to_timestamp = req['to_timestamp']
                except:
                    pass

                # print the command before the request
                print(('https://poloniex.com/public?command=returnChartData&currencyPair=' + str(req['currencyPair']) + '&start=' + str(from_timestamp) + '&end=' + str(to_timestamp) + '&period=14400'))
                ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=returnChartData&currencyPair=' + str(req['currencyPair']) + '&start=' + str(from_timestamp) + '&end=' + str(to_timestamp) + '&period=14400'), timeout = self.socket_timeout)
                return json.loads(ret.read())

            elif(command == "returnCurrencies"):
                ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=returnCurrencies'), timeout = self.socket_timeout)
                return json.loads(ret.read())
            # End
            elif(command == "returnMarketTradeHistory"):
                ret = urllib.request.urlopen(urllib.request.Request('http://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(req['currencyPair'])), timeout = self.socket_timeout)
                return json.loads(ret.read())
            else:
                req['command'] = command
                req['nonce'] = int(time.time()*1000)
                post_data = urllib.parse.urlencode(req)

                sign = hmac.new(self.Secret, post_data, hashlib.sha512).hexdigest()
                headers = {
                    'Sign': sign,
                    'Key': self.APIKey
                }

                ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/tradingApi', post_data, headers), timeout = self.socket_timeout)
                jsonRet = json.loads(ret.read())
                return self.post_process(jsonRet)
        except urllib.error.HTTPError as e:
            Logger.error('HTTPError = ' + str(e.code))
            return ''
        except urllib.error.URLError as e:
            Logger.error('URLError = ' + str(e.reason))
            return ''
        except Exception:
            import traceback
            Logger.error('generic exception: ' + traceback.format_exc())
            return ''

    def returnTicker(self):
        return self.api_query("returnTicker")

    def return24hVolume(self):
        return self.api_query("return24hVolume")

    def returnChartData (self, currencyPair):
        """
        Add API call for Candlestick Chart Data (4/5/2015 - Efthimis)
        Returns candlestick chart data. Require GET parameters are "currencyPair", "period"
        (candlestick period in seconds; valid values are 300, 900, 1800, 7200, 14400, and 86400),
        "start", and "end". "Start" and "end" are given in UNIX timestamp format
        and used to specify the date range for the data returned.
        returnChartData --> Gets only the last day
        returnFullChartData --> Gets all historical data till today. This will run once for the
        creation of the json objects, in order
        for the program to be more sufficient and lightweight, by skipping the large API replies.
        Begin
        :param currencyPair: The currency pair e.g. "BTC_XCP"
        :return: json data
        """
        return self.api_query("returnChartData", {'currencyPair': currencyPair})

    def returnFullChartData (self, currencyPair = '', from_timestamp='', to_timestamp = ''):
        """
        To be run once with the default from_timestamp and to_timestamp values - when we want to get
        full historical data. Else if we want historical data of a specific period then we give the
        from and to values as timestamp
        :param currencyPair: The currency pair e.g. "BTC_XCP"
        :param from_timestamp: Unix timestamp value
        :param to_timestamp: Unix timestamp value
        :return: json data
        """
        req={}
        if currencyPair == '':
            Logger.error('[API_poloniex.returnFullChartData]: CurrencyPair was not defined. Exiting')
            exit(1)
        req['currencyPair'] = currencyPair

        if from_timestamp != '':
            req['from_timestamp'] = from_timestamp

        if to_timestamp != '':
            req['to_timestamp'] = to_timestamp

        return self.api_query("returnFullChartData", req)

    def returnCurrencies(self):
        return self.api_query('returnCurrencies')         
    # End

    def returnOrderBook (self, currencyPair):
        return self.api_query("returnOrderBook", {'currencyPair': currencyPair})

    def returnMarketTradeHistory (self, currencyPair):
        return self.api_query("returnMarketTradeHistory", {'currencyPair': currencyPair})

    def returnBalances(self):
        """
        Returns all of your balances.
        Outputs:
        {"BTC":"0.59098578","LTC":"3.31117268", ... }
        :return: dictionary
        """
        return self.api_query('returnBalances')

    def returnOpenOrders(self,currencyPair):
        """
        Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP"
        Inputs:
        currencyPair  The currency pair e.g. "BTC_XCP"
        Outputs:
        orderNumber   The order number
        type          sell or buy
        rate          Price the order is selling or buying at
        Amount        Quantity of order
        total         Total value of order (price * quantity)
        :param currencyPair: The currency pair e.g. "BTC_XCP"
        :return: json data
        """
        return self.api_query('returnOpenOrders',{"currencyPair":currencyPair})

    def returnTradeHistory(self,currencyPair):
        """
        Returns your trade history for a given market, specified by the "currencyPair" POST parameter
         Inputs:
        currencyPair  The currency pair e.g. "BTC_XCP"
        Outputs:
        date          Date in the form: "2014-02-19 03:44:59"
        rate          Price the order is selling or buying at
        amount        Quantity of order
        total         Total value of order (price * quantity)
        type          sell or buy
        :param currencyPair: The currency pair e.g. "BTC_XCP"
        :return: json data
        """
        return self.api_query('returnTradeHistory',{"currencyPair":currencyPair})

    def buy(self,currencyPair,rate,amount):
        """
        Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
        Inputs:
        currencyPair  The curreny pair
        rate          price the order is buying at
        amount        Amount of coins to buy
        Outputs:
        orderNumber   The order number
        :param currencyPair: The currency pair e.g. "BTC_XCP"
        :param rate:
        :param amount:
        :return: json data
        """
        return self.api_query('buy',{"currencyPair":currencyPair,"rate":rate,"amount":amount})

    def sell(self,currencyPair,rate,amount):
        """
        Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
        Inputs:
        currencyPair  The curreny pair
        rate          price the order is selling at
        amount        Amount of coins to sell
        Outputs:
        orderNumber   The order number
        :param currencyPair: The currency pair e.g. "BTC_XCP"
        :param rate:
        :param amount:
        :return:
        """
        return self.api_query('sell',{"currencyPair":currencyPair,"rate":rate,"amount":amount})

    def cancel(self,currencyPair,orderNumber):
        """
        Cancels an order you have placed in a given market. Required POST parameters are "currencyPair" and "orderNumber".
        Inputs:
        currencyPair  The curreny pair
        orderNumber   The order number to cancel
        Outputs:
        succes        1 or 0
        :param currencyPair: The currency pair e.g. "BTC_XCP"
        :param orderNumber:
        :return:
         """
        return self.api_query('cancelOrder',{"currencyPair":currencyPair,"orderNumber":orderNumber})

    def withdraw(self, currency, amount, address):
        """
        Immediately places a withdrawal for a given currency, with no email confirmation. In order to use this method, the withdrawal privilege must be enabled for your API key. Required POST parameters are "currency", "amount", and "address". Sample output: {"response":"Withdrew 2398 NXT."}
        Inputs:
        currency      The currency to withdraw
        amount        The amount of this coin to withdraw
        address       The withdrawal address
        Outputs:
        response      Text containing message about the withdrawal
        :param currency: The currency pair e.g. "BTC_XCP"
        :param amount:
        :param address:
        :return:
        """
        return self.api_query('withdraw',{"currency":currency, "amount":amount, "address":address})

    def get_poloniex_active_currencies(self):
        active_currencies=[]
        try:
            for k,v in list(self.returnCurrencies().items()):
                if type(v) is type({}):
                    if v['disabled'] == 0 and v['delisted'] == 0:
                        active_currencies.append('BTC_' + str(k))
            active_currencies = sorted(active_currencies)
            return active_currencies
        except:
            Logger.info('[API_poloniex.update_all_historical_data_to_json]: Connection failure. Exiting...')
            pass

    def update_specific_historical_data_to_json(self, currency, data_period=14400, from_timestamp=9999999999,dirname='poloniex_output'):
        f.create_dir(dirname)
        #currency = ["BTC_XMR","BTC_ETH","BTC_MAID","BTC_EXP"]

        # from_timestamp will be provided by the user form
        if from_timestamp == 'All':
            # Create Unix timestamp
            from_timestamp = createTimeStamp("2012-01-01 00:00:00")

        elif from_timestamp == '1m':
            # 1 month
            one_month = datetime.now() - timedelta(days=30)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(one_month.timetuple()))

        elif from_timestamp == '2w':
            # 2 weeks
            two_weeks = datetime.now() - timedelta(days=14)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(two_weeks.timetuple()))

        elif from_timestamp == '1w':
            # 1 week
            one_week = datetime.now() - timedelta(days=7)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(one_week.timetuple()))

        elif from_timestamp == '4d':
            # 4 days
            four_days = datetime.now() - timedelta(days=4)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(four_days.timetuple()))

        elif from_timestamp == '2d':
            # 2 days
            two_days = datetime.now() - timedelta(days=2)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(two_days.timetuple()))

        elif from_timestamp == '1d':
            # 1 day
            one_day = datetime.now() - timedelta(days=1)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(one_day.timetuple()))

        elif from_timestamp == '8h':
            # 8 hours
            eight_hours = datetime.now() - timedelta(hours=8)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(eight_hours.timetuple()))

        elif from_timestamp == '6h':
            # 6 hours
            six_hours = datetime.now() - timedelta(hours=6)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(six_hours.timetuple()))

        elif from_timestamp == '2h':
            # 2 hours
            two_hours = datetime.now() - timedelta(hours=2)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(two_hours.timetuple()))

        elif from_timestamp == '1h':
            # 1 hour
            one_hour = datetime.now() - timedelta(hours=1)
            # Create Unix timestamp
            from_timestamp = int(time.mktime(one_hour.timetuple()))

        # To future day
        to_timestamp = 9999999999
        #to_timestamp = createTimeStamp(str(date.today()) + " 24:00:00")
        print(('https://poloniex.com/public?command=returnChartData&resolution=auto&currencyPair=' + str(currency) + '&start=' + str(from_timestamp) + '&end=' + str(to_timestamp) + '&period=' + str(data_period)))
        #url_string = ('https://poloniex.com/public?command=returnChartData&currencyPair=' + str(currency) + '&start=' + str(from_timestamp) + '&end=' + str(to_timestamp) + '&period=' + str(data_period))
        ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/public?command=returnChartData&resolution=auto&currencyPair=' + str(currency) + '&start=' + str(from_timestamp) + '&end=' + str(to_timestamp) + '&period=' + str(data_period)), timeout = self.socket_timeout)
        #json_data = json.loads(ret.read())
        json_data = json.load(ret)

        #return json_data

        if json_data == '':
            #Logger.error('[API_poloniex.update_specific_historical_data_to_json]: Connection failure. Exiting...')
            #return
            Logger.info('[API_poloniex.update_specific_historical_data_to_json]: Connection failure. Exiting...')
            #return
        if re.search( r'error', json.dumps(json_data), re.M|re.I):
            Logger.info('[API_poloniex.update_specific_historical_data_to_json]: Data from currency ' + currency + ' at the moment are not available.')
        if json_data != '':
            # This saves the file into disk
            Logger.info('Fetching Data successful. Saving .json to disk')
            #f.file_save_json_contents(dirname + f.PATH_SEPARATOR + currency + '.json', json_data)
            f.file_save_json_contents(dirname + f.PATH_SEPARATOR + str(currency) + '_from_' + str(from_timestamp) + '_period_' + str(data_period) + '.json', json_data)
            complete_json_filename = dirname + f.PATH_SEPARATOR + str(currency) + '_from_' + str(from_timestamp) + '_period_' + str(data_period) + '.json'
            return complete_json_filename


    def update_all_historical_data_to_json(self, dirname='', data_period=14400):
        f.create_dir(dirname)
#        x = ["BTC_XMR","BTC_ETH","BTC_MAID","BTC_EXP"]
        try:
            for currency in self.get_poloniex_active_currencies():
#            for currency in x:
                if f.is_file_exist(dirname + f.PATH_SEPARATOR + currency + '.json'):
                    json_data = f.file_get_json_contents(dirname + f.PATH_SEPARATOR + currency + '.json')
                    try:
                        if int(json_data[-1]['date'] + data_period) < int(time.time()):
                            new_json_data = self.returnFullChartData(currency, from_timestamp = (json_data[-1]['date'] + data_period))
                            if new_json_data == '':
                                Logger.error('[API_poloniex.update_all_historical_data_to_json]: Connection failure. Exiting...')
                                return
                            if new_json_data[-1]['date'] == 0:
                                continue
                        else:
                            continue
                    except KeyError:
                        Logger.error('[API_poloniex.update_all_historical_data_to_json]: The key data was not found in file ' + dirname + f.PATH_SEPARATOR + currency + '.json. Continuing to the next file.')
                        continue
                    if re.search( r'error', json.dumps(new_json_data), re.M|re.I):
                        Logger.info('[API_poloniex.update_all_historical_data_to_json]: Data from currency ' + currency + ' at the momment are not available. Continuing to the next currency.')
                        continue
                    if new_json_data != '':
                        f.file_save_json_contents(dirname + f.PATH_SEPARATOR + currency + '.json', new_json_data)
                else:
                    json_data = self.returnFullChartData(currency)
                    if json_data == '':
                        Logger.error('[API_poloniex.update_all_historical_data_to_json]: Connection failure. Exiting...')
                        return
                    if re.search( r'error', json.dumps(json_data), re.M|re.I):
                        Logger.info('[API_poloniex.update_all_historical_data_to_json]: Data from currency ' + currency + ' at the momment are not available. Continuing to the next currency.')
                        continue
                    if json_data != '':
                        f.file_save_json_contents(dirname + f.PATH_SEPARATOR + currency + '.json', json_data)
        except:
            Logger.error('[API_poloniex.update_all_historical_data_to_json]: Connection failure. Exiting...')
            return

    def extract_values_from_json(self, json_dir='', output_dir=''):
        if json_dir == '' or output_dir == '':
            Logger.error('[API_poloniex.extract_values_from_json] Invalid input to function. Exiting...')
            return
        f.create_dir(output_dir)
        for filename in os.listdir(json_dir):
            print(filename)
            if (f.file_get_contents(json_dir + f.PATH_SEPARATOR + filename) != "{\"error\": \"Invalid currency pair.\"}") and (f.file_get_contents(json_dir + f.PATH_SEPARATOR + filename) != ""):
                file_with_parsed_values = open(json_dir + f.PATH_SEPARATOR + filename + '.txt', "w")
                #file_with_parsed_values.write('BTC_FIBRE.json')
                fileinjson =  f.file_get_json_contents(json_dir + f.PATH_SEPARATOR + filename)
                for item in fileinjson:
                    file_with_parsed_values.write("DATE ==> " + str(datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d'))  + "\n")
                    file_with_parsed_values.write("HIGH ==> " + str(item['high']) + "\n")
                    file_with_parsed_values.write("LOW ==> " + str(item['low']) + "\n")
                    file_with_parsed_values.write("CLOSE ==> " + str(item['close']) + "\n")
                    file_with_parsed_values.write("*****************************" + "\n")
                file_with_parsed_values.close()

    def write_all_data_to_excel(self, historic_data_dir):
        Logger.info('[API_poloniex.write_all_data_to_excel] Generating excel report...')
        # Create Workbook
        workbook = xlsxwriter.Workbook('ubicrypt_poloniex.xlsx')
        # Add the worksheet with its appropriate name
        worksheet = workbook.add_worksheet('Poloniex')
        #Write the headers
        # Add bold format
        format = workbook.add_format()
        format.set_bold()
        # Widen column space
        worksheet.set_column('A:ZZ', 15)
        # Point to the B1 cell for the first currency name
        row = 0
        column = 1
        next_currency_flag = 0
        # Start importing the data
        for filename in os.listdir(historic_data_dir):
            # TODO - This if maybe need to be excluded or maybe not I am not sure. We must have a meeting to decide.
            if (f.file_get_contents(historic_data_dir + f.PATH_SEPARATOR + filename) != "{\"error\": \"Invalid currency pair.\"}") and (f.file_get_contents(historic_data_dir + f.PATH_SEPARATOR + filename) != ''):
                fileinjson =  json.loads(open(historic_data_dir + f.PATH_SEPARATOR + filename).read())
                # new_filename = taking the currency name out of the filename
                new_filename = filename.replace('.json', '')
                new_filename = new_filename.replace('BTC_', '')
                if next_currency_flag != 0 :
                    row = 0
                    column  =  column + 5
                worksheet.write(row, column, new_filename, format)
                # Point to the A2 cell for the first currency Date
                row = row + 1
                column = column - 1
                worksheet.write(row, column, 'Date', format)
                # Point to the B2 cell for the first currency High
                column = column + 1
                worksheet.write(row, column, 'High', format)
                # Point to the C2 cell for the first currency Low
                column = column + 1
                worksheet.write(row, column, 'Low', format)
                # Point to the D2 cell for the first currency Close
                column = column + 1
                worksheet.write(row, column, 'Close', format)
                # The next points for the first currency to A3 cell, it would be the starting place for our parsing
                row = row + 1
                column = column - 3
                for item in fileinjson:
                    # Goes like this: worksheet.write(row, col, some_data)
                    worksheet.write(row, column, str(datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d')))
                    column = column + 1
                    worksheet.write(row, column, '%.8f' % (item['high']))
                    column = column + 1
                    worksheet.write(row, column, '%.8f' % (item['low']))
                    column = column + 1
                    worksheet.write(row, column, '%.8f' % (item['close']))
                    column = column - 3
                    row = row + 1
                next_currency_flag = next_currency_flag + 1
        workbook.close()
        Logger.info('[API_poloniex.write_all_data_to_excel] Finish excel report generation...')
