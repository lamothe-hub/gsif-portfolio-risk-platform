import quandl
from dashboards.calculations import preprocess, dataAccess, calculate
from dashboards.models import Portfolio
from django.contrib.auth.models import User
import queue
import datetime
import ast
import json
from pprint import pprint
from dashboards.calculations import preprocess

from pandas_datareader import data as pdr
import threading

def setup(sector):
    key = 'ZcDqZyg9kM9oVVuHFA1p'
    quandl.ApiConfig.api_key = key

    master_user = User.objects.get(username='master')
    current_portfolio = Portfolio.objects.get(owner=master_user, sector=sector)
    now = datetime.datetime.now()
    start_date = str(current_portfolio.start_date)
    end_date = str((now.strftime('%Y-%m-%d')))
    last = datetime.datetime.strptime(current_portfolio.end_date, '%Y-%m-%d')
    elapsed_time = (now - last).days
    updated_recently = False
    if elapsed_time == 0:
        updated_recently = True

    if not updated_recently:
        holdings, benchmarks = pull_portfolio(sector)
        holdings, benchmarks = pullHistoricalData(holdings, benchmarks, start_date, end_date, sector)
        holdings = calculate.dailyPercentReturnsOnHistoricalData(holdings)
        benchmarks = calculate.dailyPercentReturnsOnHistoricalData(benchmarks)
        holdings = calculate.setHoldingsWeights(holdings)
        benchmarks = calculate.findBenchmarkShares(holdings, benchmarks)

        def save_portfolio(holdings, benchmarks, sector):
            master_user = User.objects.get(username='master')
            current_portfolio = Portfolio.objects.get(owner=master_user, sector=sector)
            current_portfolio.holdings = json.dumps(holdings)
            current_portfolio.benchmarks = json.dumps(benchmarks)
            current_portfolio.end_date = str((now.strftime('%Y-%m-%d')))
            current_portfolio.save()
            print(sector + " portfolio SAVED")

        save_portfolio(holdings, benchmarks, sector)


        return holdings, benchmarks

    else:
        master_user = User.objects.get(username='master')
        current_portfolio = Portfolio.objects.get(owner=master_user, sector=sector)
        holdings = ast.literal_eval(current_portfolio.holdings)
        benchmarks = ast.literal_eval(current_portfolio.benchmarks)
        return holdings, benchmarks

    """
    Output:
    holdings, benchmark: {
        ticker: {
            historicalData: [...],
            ninetyDayData: [...],
            pdrHistoricalData: [...],
            percentDailyReturns: [...],
            shares: xx,
            weight: xx,
        }
    }
    """
def pull_portfolio(sector_input):
    master_user = User.objects.get(username='master')
    try:
        port = Portfolio.objects.get(owner=master_user, sector=sector_input)
        db_holdings = ast.literal_eval(port.holdings)
        db_benchmarks = ast.literal_eval(port.benchmarks)
        holdings = {}
        benchmarks = {}
        for h in db_holdings:
            if h != 'dates':
                holdings[h] = {}
                holdings[h]['shares'] = float(db_holdings[h]['shares'])
        for b in db_benchmarks:
            benchmarks[b] = {}
            benchmarks[b]['weight'] = float(db_benchmarks[b]['weight'])
        return holdings, benchmarks
        """
        OUTPUT: holdings have share counts, benchmarks have weights.
        holdings: {
            ticker1: {
                shares: xx
            },
            ticker2: {
                shares: xx
            },
            ...
        },
        benchmakrs: {
            ticker1: {
                weight: xx
            },
            ticker2: {
                weight: xx
            },
            ...
        }
        """
    except:
        print("[pull_portfolio]: Could not pull master portfolio for sector: " + sector_input)
        return {},{}

def pullHistoricalAnd90Day(holdings, benchmarks, start_date, end_date, sector):

    def assign_data_to_ticker(holdings, benchmarks, data):
        for ticker in list(holdings.keys()):
            holdings[ticker]['historicalData'] = data[ticker]['historicalData']
            holdings[ticker]['ninetyDayData'] = data[ticker]['ninetyDayData']
        for ticker in list(benchmarks.keys()):
            benchmarks[ticker]['historicalData'] = data[ticker]['historicalData']
            benchmarks[ticker]['ninetyDayData'] = data[ticker]['ninetyDayData']
        return holdings, benchmarks

    def worker(num):

        def ensure_90_days(ticker, ninety_day_start, start_date, end_date):
            yahoo_data = pdr.get_data_yahoo(ticker, ninety_day_start, end_date)
            difference = 90 - len(list(yahoo_data['Close'][:start_date]))
            if difference > 0:
                ninety_day_start = ninety_day_start - datetime.timedelta(days=difference)
                yahoo_data = ensure_90_days(ticker, ninety_day_start, start_date, end_date)
            return yahoo_data

        while True:
            item = q.get()
            if item is None:
                break
            ticker, ninety_day_start, start_date, end_date = item
            start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            ninety_day_start = start - datetime.timedelta(days=129)
            try:
                yahoo_data = ensure_90_days(ticker, ninety_day_start, start_date, end_date)
            except:
                print("ERROR: ensure_90_days failed for " + str(ticker))
            try:
                data[ticker] = {}
                data[ticker]['ninetyDayData'] = list(yahoo_data['Close'][:start_date])
                data[ticker]['historicalData'] = list(yahoo_data['Close'][start_date:])
            except:
                print("ERROR: failed to assign data to " + str(ticker))

            print(str(ticker) + ": SUCCESS")
            q.task_done()

    requests = []
    start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    ninety_day_start = start - datetime.timedelta(days=129)
    for ticker in holdings.keys():
        requests.append((ticker, ninety_day_start, start_date, end_date))
    for ticker in benchmarks.keys():
        if ticker not in holdings.keys():
            requests.append((ticker, ninety_day_start, start_date, end_date))

    q = queue.Queue()
    data = {}
    threads = []
    thread_count = len(requests)
    print("Initilizing " + str(thread_count) + " data fetch threads for " + str(sector))
    for i in range(thread_count):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)

    for item in requests:
        q.put(item)

    q.join()

    for i in range(len(threads)):
        q.put(None)
    for t in threads:
        t.join()


    return assign_data_to_ticker(holdings, benchmarks, data)

def pullHistoricalData(holdings, benchmarks, start_date, end_date, sector):
    def assign_data_to_ticker(holdings, benchmarks, data):
        for ticker in list(holdings.keys()):
            holdings[ticker]['historicalData'] = data[ticker]['historicalData']
        for ticker in list(benchmarks.keys()):
            benchmarks[ticker]['historicalData'] = data[ticker]['historicalData']

        dates = []
        for date in data['dates']:
            dates.append(date.strftime('%m-%d'))

        holdings['dates'] = dates
        return holdings, benchmarks

    def worker(num):
        while True:
            item = q.get()
            if item is None:
                break
            ticker, start_date, end_date = item
            print("ticker, start_date, end_date: " + str(ticker) + ', ' + str(start_date) + ', ' + str(end_date))
            try:
                yahoo_data = pdr.get_data_yahoo(ticker, start_date, end_date)
            except:
                print("ERROR: yahoo request failed for " + str(ticker))
            try:
                if data['dates'] == []:
                    data['dates'] = list(yahoo_data.index)
                data[ticker] = {}
                data[ticker]['historicalData'] = list(yahoo_data['Close'][start_date:])
            except:
                print("ERROR: failed to assign data to " + str(ticker))
            print(str(ticker) + ": SUCCESS")
            q.task_done()

    requests = []
    for ticker in holdings.keys():
        requests.append((ticker, start_date, end_date))
    for ticker in benchmarks.keys():
        if ticker not in holdings.keys():
            requests.append((ticker, start_date, end_date))
    q = queue.Queue()
    data = {}
    data['dates'] = []
    threads = []
    thread_count = len(requests)
    print("Initilizing " + str(thread_count) + " data fetch threads for " + str(sector))
    for i in range(thread_count):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)

    for item in requests:
        q.put(item)

    q.join()

    for i in range(len(threads)):
        q.put(None)
    for t in threads:
        t.join()
    return assign_data_to_ticker(holdings, benchmarks, data)

def tev_setup(sector, start_date, end_date):
    def pull_implied_vols(holdings, benchmarks):
        key = 'ZcDqZyg9kM9oVVuHFA1p'
        quandl.ApiConfig.api_key = key
        implied_vols = {}

        for holding in holdings.keys():
            # pull implied vol and set in the implied_vols dict
            formatted_ticker = 'VOL/' + holding
            try:
                data = quandl.get(formatted_ticker, start_date=start_date, end_date=start_date)
                implied_vol = data.loc[start_date,'Hv90']
                implied_vols[holding] = implied_vol
            except:
                print("FAILED: Could not pull implied vol for " + holding)

        for benchmark in benchmarks.keys():
            # pull implied vol from quandl and assign in the implied_vols dict
            formatted_ticker = 'VOL/' + benchmark
            try:
                data = quandl.get(formatted_ticker, start_date=start_date, end_date=start_date)
                implied_vol = data.loc[start_date,'Hv90']
                implied_vols[benchmark] = implied_vol
            except:
                print("FAILED: Could not pull implied vol for " + benchmark)

            for holding in holdings:
                try:
                    holdings[holding]['impliedVol'] = implied_vols[holding]
                except:
                    holdings[holding]['impliedVol'] = 0.25
            for benchmark in benchmarks:
                try:
                    benchmarks[benchmark]['impliedVol'] = implied_vols[benchmark]
                except:
                    benchmarks[benchmark]['impliedVol'] = 0.25

            return holdings, benchmarks
    key = 'ZcDqZyg9kM9oVVuHFA1p'
    quandl.ApiConfig.api_key = key

    holdings, benchmarks = pull_portfolio(sector)
    holdings, benchmarks = pull_implied_vols(holdings, benchmarks)
    holdings, benchmarks = pullHistoricalAnd90Day(holdings, benchmarks, start_date, end_date, sector)
    holdings = calculate.dailyPercentReturnsOnNinetyDay(holdings)
    benchmarks = calculate.dailyPercentReturnsOnNinetyDay(benchmarks)
    holdings = calculate.dailyPercentReturnsOnHistoricalData(holdings)
    benchmarks = calculate.dailyPercentReturnsOnHistoricalData(benchmarks)
    holdings = calculate.setHoldingsWeights(holdings)
    benchmarks = calculate.findBenchmarkShares(holdings, benchmarks)
    return holdings, benchmarks
