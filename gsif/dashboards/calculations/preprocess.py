import quandl
from dashboards.calculations import preprocess, dataAccess, calculate
from dashboards.models import Portfolio
from django.contrib.auth.models import User
import queue
import datetime
import ast
import json
import pprint


def setup_entire_portfolio(portfolio):
    # Goal: pull all of the sectors shares:count
    # Retrieve historical and 90 day data in an optimal way
    # return an array for the holdings of each sector
    # return an array for the benchmarks of each sector
    # TODO: this is going to be a big todo, since we should optimize with the file system first.

    key = 'b_-29a4sXyvQwH-SVPFy'
    quandl.ApiConfig.api_key = key

    def pull_implied_vols(holdlings, benchmarks):
        implied_vols = {
            'SEP':.21952,
            'FANG':.3062,
            'AES':.32198,
            'XLE':.19971,
        }
        for holding in holdings:
            try:
                holdings[holding]['impliedVol'] = implied_vols[holding]
            except:
                print("Setting dummy implied vol for " + holding)
                holdings[holding]['impliedVol'] = 0.25
        for benchmark in benchmarks:
            try:
                benchmarks[benchmark]['impliedVol'] = implied_vols[benchmark]
            except:
                print("Setting dummy implied vol for " + benchmark)
                benchmarks[benchmark]['impliedVol'] = 0.25

        return holdings, benchmarks

    portfolio_array = []
    for sector in ['energy', 'healthcare', 'tech','financials','consumers','industrials']:
        holdings, benchmarks = pull_portfolio(sector)
        portfolio_array.append((sector, holdings, benchmarks))


    # pull implied vols: TODO: fix this later:
    for i in range(len(portfolio_array)):
        sector, holdings, benchmarks = portfolio_array[i]
        new_holdings, new_benchmarks = pull_implied_vols(holdings, benchmarks)
        portfolio_array[i] = (sector, new_holdings, new_benchmarks)

    print("")

    """
    holdings, benchmarks = pull_implied_vols(holdings, benchmarks)
    print("holdings: ")
    print(holdings)
    print("benchmarks: ")
    print(benchmarks)

    holdings, benchmarks = dataAccess.pullHistoricalData(holdings, benchmarks, '2018-02-16', '2018-03-16')


    holdings = calculate.dailyPercentReturnsOnNinetyDay(holdings)
    benchmarks = calculate.dailyPercentReturnsOnNinetyDay(benchmarks)

    holdings = calculate.dailyPercentReturnsOnHistoricalData(holdings)
    benchmarks = calculate.dailyPercentReturnsOnHistoricalData(benchmarks)

    holdings = calculate.setHoldingsWeights(holdings)
    benchmarks = calculate.findBenchmarkShares(holdings, benchmarks)
    return holdings, benchmarks
    """




def setup(sector, start_date='2018-01-01', end_date='2018-06-01'):
    key = 'ZcDqZyg9kM9oVVuHFA1p'
    quandl.ApiConfig.api_key = key


    implied_vols = {}

    def pull_implied_vols(holdlings, benchmarks):
        for holding in holdings:
            print("holdings: about to pull implied vol for " + holding)
            # pull implied vol and set in the implied_vols dict
            formatted_ticker = 'VOL/' + holding
            try:
                data = quandl.get(formatted_ticker, start_date=start_date, end_date=start_date)
                implied_vol = data.loc[start_date,'Hv90']
                implied_vols[holding] = implied_vol
            except:
                print("FAILED: Could not pull implied vol for " + holding)

        for benchmark in benchmarks:
            print("benchmarks: about to pull implied vol for " + benchmark)
            # pull implied vol from quandl and assign in the implied_vols dict
            formatted_ticker = 'VOL/' + benchmark
            try:
                data = quandl.get(formatted_ticker, start_date=start_date, end_date=start_date)
                implied_vol = data.loc[start_date,'Hv90']
                implied_vols[benchmark] = implied_vol
            except:
                print("FAILED: Could not pull implied vol for " + benchmark)
        """
        implied_vols = {
            'SEP':.21952,
            'FANG':.3062,
            'AES':.32198,
            'XLE':.19971,
        }
        """
        for holding in holdings:
            try:
                holdings[holding]['impliedVol'] = implied_vols[holding]
            except:
                print("Setting dummy implied vol for " + holding)
                holdings[holding]['impliedVol'] = 0.25
        for benchmark in benchmarks:
            try:
                benchmarks[benchmark]['impliedVol'] = implied_vols[benchmark]
            except:
                print("Setting dummy implied vol for " + benchmark)
                benchmarks[benchmark]['impliedVol'] = 0.25

        return holdings, benchmarks

    holdings, benchmarks = pull_portfolio(sector)

    # pull implied vols: TODO: fix this later:
    #holdings, benchmarks = pull_implied_vols(holdings, benchmarks)
    holdings, benchmarks = dataAccess.pullHistoricalData(holdings, benchmarks, start_date, end_date)


    holdings = calculate.dailyPercentReturnsOnNinetyDay(holdings)
    benchmarks = calculate.dailyPercentReturnsOnNinetyDay(benchmarks)

    holdings = calculate.dailyPercentReturnsOnHistoricalData(holdings)
    benchmarks = calculate.dailyPercentReturnsOnHistoricalData(benchmarks)

    holdings = calculate.setHoldingsWeights(holdings)
    benchmarks = calculate.findBenchmarkShares(holdings, benchmarks)
    return holdings, benchmarks

def pull_portfolio(sector_input):
    master_user = User.objects.get(username='master')
    try:
        port = Portfolio.objects.get(owner=master_user, sector=sector_input)
        db_holdings = ast.literal_eval(port.holdings)
        db_benchmarks = ast.literal_eval(port.benchmarks)
        holdings = {}
        benchmarks = {}
        for h in db_holdings:
            holdings[h] = {}
            holdings[h]['shares'] = float(db_holdings[h])
        for b in db_benchmarks:
            benchmarks[b] = {}
            benchmarks[b]['weight'] = float(db_benchmarks[b])
        #print(holdings)
        #print(benchmarks)
        return holdings, benchmarks
    except:
        print("[pull_portfolio]: Could not pull master portfolio for sector: " + sector_input)
        return {},{}




def setup_from_csv():
    # NOTE: exel sheet is taking close data, while mine is taking adj close...

    key = 'b_-29a4sXyvQwH-SVPFy'
    quandl.ApiConfig.api_key = key
    holdings, benchmarks = preprocess.setDefaultPortflioAndBenchmark()
    # ---------------------------------------------------------------
    holdings = retrieveInputCopiedFromSpreadsheet(holdings)
    benchmarks = retrieveInputCopiedFromSpreadsheet(benchmarks)
    # ---------------------------------------------------------------

    print("Inside setup_from_csv: ")

    for ticker in holdings:
        print(ticker)

        print(holdings[ticker]['ninetyDayData'])

    holdings = calculate.dailyPercentReturnsOnNinetyDay(holdings)
    benchmarks = calculate.dailyPercentReturnsOnNinetyDay(benchmarks)



    return holdings, benchmarks

def saveToFile(holdings, benchmarks):
    data = json.dumps(holdings, indent=4)
    holdingsFile = open("holdings.json", "w")
    holdingsFile.write(data)
    holdingsFile.close()

    data = json.dumps(benchmarks, indent=4)
    holdingsFile = open("benchmarks.json", "w")
    holdingsFile.write(data)
    holdingsFile.close()

def loadFromFile():
    holdingsData = open("holdings.json").read()
    holdings = json.loads(holdingsData)

    benchmarkData = open("benchmarks.json").read()
    benchmarks = json.loads(benchmarkData)

    return holdings, benchmarks

def setDefaultPortflioAndBenchmark():
    # This is how the holdings will be formatted. We will later add historical data to this obejct for each respective holding.
    holdings = {
        'SEP':{
            #'weight':.1270,
            'impliedVol': .21952,
            'shares': 350.25
        },
        'FANG':{
            #'weight':.1840,
            'impliedVol': .3062,
            'shares': 146.6
        },
        'AES': {
            #'weight': .0890,
            'impliedVol': .32198,
            'shares': 821.03

        },
        'XLE': {
            #'weight': .60,
            'impliedVol': .19971,
            'shares': 891.40
        },
    }
    benchmarks = {
        'XLE': {
            'weight': 1,
            'impliedVol': .19971,
            #'shares': 1485.66
        },
    }
    return (holdings, benchmarks)

def retrieveInputCopiedFromSpreadsheet(holdings):
    for holding in holdings:
        filename = 'files/90day/' + holding + '.csv'
        file = open(filename, 'r')
        histData = []
        for line in file:
            lineArray = line.split(',')
            histData.append(float(lineArray[0]))
        holdings[holding]['ninetyDayData'] = histData

    return holdings


def adjCloseFromCSV(tickerName):
    #use this for data copied in from yahoo finance
    filename = 'files/' + tickerName + '.csv'
    file = open(filename, 'r')
    histData = []
    for line in file:
        lineArray = line.split(',')
        histData.append(float(lineArray[5]))

    return histData





"""
# outdated as of Yahoo finance implementation:

def historical90DayFromCSV(tickerName):

    filename = 'files/90day/' + tickerName + '.csv'
    i = 0
    histData = []
    for line in reversed(open(filename).readlines()):
        if i < 90:
            histData.append(float(line.split(',')[5]))
        i += 1

    reverseArray = []
    for price in reversed(histData):
        reverseArray.append(price)

    return reverseArray

"""
