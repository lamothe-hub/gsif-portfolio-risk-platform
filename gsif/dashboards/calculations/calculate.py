import numpy as np
import math
import ast
from dashboards.models import Portfolio
from django.contrib.auth.models import User
from dashboards.calculations import preprocess, clean_preprocess


def absoluteReturnsForAllMasterSectors(request):
    # calculte the absolute returns for all 6 master sectors combined

    energyh, energyb = clean_preprocess.setup('energy')
    consumersh, consumersb = clean_preprocess.setup('consumers')
    financialsh, financialsb = clean_preprocess.setup('financials')
    techh, techb = clean_preprocess.setup('tech')
    industrialsh, industrialsb = clean_preprocess.setup('industrials')
    healthcareh, healthcareb = clean_preprocess.setup('healthcare')
    holdings_array = [energyh,consumersh,financialsh,techh,industrialsh,healthcareh]
    benchmarks_array = [energyb,consumersb,financialsb,techb,industrialsb,healthcareb]

    def set_graph_data_for_sectors(holdings_array, benchmarks_array):
        sectors = ['energy', 'consumers', 'financials', 'tech', 'industrials', 'healthcare']
        for i in range(6):
            request.session[sectors[i] + '_h_returns'] = absoluteReturns(holdings_array[i])
            request.session[sectors[i] + '_b_returns'] = absoluteReturns(benchmarks_array[i])
            if i == 0:
                request.session['sector_x'] = [i for i in range(len(absoluteReturns(benchmarks_array[i])))]

    set_graph_data_for_sectors(holdings_array, benchmarks_array)

    dates = techh['dates']
    print(dates)

    first_iteration = True
    try:
        for holdings in holdings_array:
            current_returns = absoluteReturns(holdings)
            if first_iteration:
                total_returns = current_returns
                first_iteration = False
            else:
                for i in range(len(total_returns)):
                    total_returns[i] += current_returns[i]
    except:
        total_returns = []
        current_returns = []
    first_iteration = True
    benchmark_returns = []
    try:
        for benchmarks in benchmarks_array:
            current_returns = absoluteReturns(benchmarks)
            if first_iteration:
                benchmark_returns = current_returns
                first_iteration = False
            else:
                for i in range(len(benchmark_returns)):
                    benchmark_returns[i] += current_returns[i]
    except:
        benchmark_returns = []
        current_returns = []
    request.session['holdings_data'] = total_returns
    request.session['benchmarks_data'] = benchmark_returns
    absolute_x = [i for i in range(len(total_returns) -1)]
    request.session['absolute_x'] = absolute_x
    request.session['dates_axis'] = dates[:-1]
    request.session['test_letters'] = ['a','b','c','d','e','f','g','h','i']

    print("Size of dates_Axis: " + str(len(request.session['dates_axis'])))
    print("Size of absolute_x: " + str(len(request.session['absolute_x'])))
    print(request.session['dates_axis'])
    print(request.session['absolute_x'])


def absoluteReturns(holdings):
    # this will calculate the absolute returns for a single sector
    cumulativeReturns = []
    i = 0
    for ticker in holdings:
        if ticker != 'dates':
            historicalPriceArray = holdings[ticker]['historicalData']
            for day in historicalPriceArray:

                value = float(holdings[ticker]['shares']) * float(day)
                if i > len(cumulativeReturns) - 1:
                    cumulativeReturns.append(value)
                else:
                    cumulativeReturns[i] = value + cumulativeReturns[i]
                i += 1
            i = 0
    return cumulativeReturns

def excessReturns(holdings, benchmarks):
    holdingsValueArray = absoluteReturns(holdings)
    benchmarksValueArray = absoluteReturns(benchmarks)
    excessReturnsArray = []
    i = 0
    for day in holdingsValueArray:
        excessReturnsArray.append(holdingsValueArray[i] - benchmarksValueArray[i])
        print(holdingsValueArray[i] - benchmarksValueArray[i])
        i += 1

    return excessReturnsArray

def cumulativeReturnsByPercentage(holdings, benchmarks):
    benchmarkAbsolute = absoluteReturns(benchmarks)
    holdingsAbsolute = absoluteReturns(holdings)
    percentReturns = []
    i = 1
    while i < len(holdingsAbsolute):
        holdingsPercentChange = (holdingsAbsolute[i] - holdingsAbsolute[0]) / holdingsAbsolute[0]
        benchmarksPercentChange = (benchmarkAbsolute[i] - benchmarkAbsolute[0]) / benchmarkAbsolute[0]
        percentReturns.append((holdingsPercentChange - benchmarksPercentChange))
        i += 1

    return percentReturns

def pdr_against_benchmark_by_shares(holdings, benchmarks):
    # KEEPER: these are the values you print against tev

    min_date_range = min(len(holdings[list(holdings.keys())[0]]['historicalData']), len(benchmarks[list(benchmarks.keys())[0]]['historicalData']))
    pdr = [0]
    for i in range(1, min_date_range):
        # get total portfolio value, TP
        # get total benchmark value, TB
        today_holdings_value = 0.0
        yesterday_holdings_value = 0.0
        for ticker in holdings:
            shares = holdings[ticker]['shares']
            today_price = holdings[ticker]['historicalData'][i]
            yesterday_price = holdings[ticker]['historicalData'][i-1]
            today_holdings_value += shares * today_price
            yesterday_holdings_value += shares * yesterday_price
        today_benchmarks_value = 0.0
        yesterday_benchmarks_value = 0.0
        for ticker in benchmarks:
            shares = benchmarks[ticker]['shares']
            today_price = benchmarks[ticker]['historicalData'][i]
            yesterday_price = benchmarks[ticker]['historicalData'][i-1]
            today_benchmarks_value += shares * today_price
            yesterday_benchmarks_value += shares * yesterday_price
        # print("today_holdings_value: " + str(today_holdings_value))
        # print("yesterday_holdings_value: " + str(yesterday_holdings_value))
        # print("today_benchmarks_value: " + str(today_benchmarks_value))
        # print("yesterday_benchmarks_value: " + str(yesterday_benchmarks_value))
        pdr.append(((today_holdings_value - yesterday_holdings_value) / yesterday_holdings_value) - ((today_benchmarks_value - yesterday_benchmarks_value) / yesterday_benchmarks_value))
    return pdr




def cumulative_returns_no_shares(holdings, benchmarks):
    holding_cumulative = 100000
    benchmark_cumulative = 100000
    benchmark_returns, holding_returns = [100000.0],[100000.0]

    i = 0
    key = list(holdings.keys())[0]
    while i < len(holdings[key]['pdrHistoricalData']):
        for ticker in holdings:
            holding_cumulative += holding_cumulative * holdings[ticker]['pdrHistoricalData'][i] * holdings[ticker]['weight']
        holding_returns.append(holding_cumulative)
        i += 1

    j = 0
    key = list(benchmarks.keys())[0]
    while j < len(benchmarks[key]['pdrHistoricalData']):
        for ticker in benchmarks:
            benchmark_cumulative += benchmark_cumulative * benchmarks[ticker]['pdrHistoricalData'][j] * benchmarks[ticker]['weight']
        benchmark_returns.append(benchmark_cumulative)
        j += 1

    final_returns = []
    k = 0

    while k < len(holding_returns):
        final_returns.append(benchmark_returns[k] - holding_returns[k] + 100000)
        k += 1

    return final_returns

def cumulative_pdr(holdings, benchmarks):
    holding_cumulative = 100000
    benchmark_cumulative = 100000
    benchmark_returns, holding_returns = [100000.0], [100000.0]

    i = 0
    key = list(holdings.keys())[0]
    while i < len(holdings[key]['pdrHistoricalData']):
        print(i)
        for ticker in holdings:
            holding_cumulative += holding_cumulative * holdings[ticker]['pdrHistoricalData'][i] * holdings[ticker][
                'weight']
        holding_returns.append(holding_cumulative)
        i += 1

    j = 0
    key = list(benchmarks.keys())[0]
    while j < len(benchmarks[key]['pdrHistoricalData']):
        for ticker in benchmarks:
            benchmark_cumulative += benchmark_cumulative * benchmarks[ticker]['pdrHistoricalData'][j] * \
                                    benchmarks[ticker]['weight']
        benchmark_returns.append(benchmark_cumulative)
        j += 1

    final_returns = []
    k = 0
    print(holding_returns)
    print(benchmark_returns)
    while k < len(holding_returns):
        print(k)
        final_returns.append(benchmark_returns[k] - holding_returns[k] + 100000)
        k += 1

    return final_returns

def tev_plot_array(holdings, tev):
    # KEEP
    # convert annual TEV to
    # 252 trading days
    # divide TEV by sqrt(252)
    # daily vol = mul by sqrt(252)
    data = [0]
    daily = tev / math.sqrt(252)
    i = 1
    while i <= len(holdings[list(holdings.keys())[0]]['pdrHistoricalData']):
        data.append(daily * math.sqrt(i))
        i += 1

    return data


def corellationMatrix(holdings, benchmarks):
    # input holdings with 90 day historical data and output corellation matrix
    # Note: this function currently uses Pearson coefficient, which is the default for np.corrcoef

    dataArray = []
    for ticker in holdings:
        #print(ticker)
        dataArray.append(holdings[ticker]['percentDailyReturns'])

    for ticker in benchmarks:
        dataArray.append(benchmarks[ticker]['percentDailyReturns'])

    return (np.corrcoef(dataArray))



def covarianceMatrix(holdings, benchmarks):
    matrix = corellationMatrix(holdings, benchmarks)

    #print("Corellation matrix: ")
    #print(matrix)
    #print("\n------------------\n")

    impliedVols = []
    for ticker in holdings:
        impliedVols.append(holdings[ticker]['impliedVol'])

    for ticker in benchmarks:
        impliedVols.append(benchmarks[ticker]['impliedVol'])

    i = 0; j = 0
    while i < (len(impliedVols)):
        while j < (len(impliedVols)):
            # TODO: ask if impliedVols should be square rooted!!
            matrix[i][j] = matrix.item(i, j) * impliedVols[i] * impliedVols[j]
            j += 1
        i += 1
        j = 0

    #print("Covariance matrix: ")
    #print(matrix)
    #print("\n------------------\n")

    return matrix  # This will be the covariance matrix using Pearson corellation coefficient in the calculation.

def trackingErrorVolatility(holdings, benchmarks):
    covMatrix = covarianceMatrix(holdings, benchmarks)
    weights = []
    for ticker in holdings:
        weights.append(holdings[ticker]['weight'])

    for ticker in benchmarks:
        weights.append(-1 * (benchmarks[ticker]['weight']))

    #print("weights: ")
    #print(weights)
    #print("\n------------------\n")


    return math.sqrt(np.matmul(np.matmul(covMatrix, weights), weights))

def setHoldingsWeights(holdings):
    # Holdings add up to 100 and benchmarks add up to 100 seperately
    # pprint.pprint(holdings)

    # Step 1) Calculate the total values for each of the holdings
    totalValueDayOne = 0
    for ticker in holdings:
        if ticker != 'dates':
            totalValueDayOne += holdings[ticker]['shares'] * holdings[ticker]["historicalData"][0]

    for ticker in holdings:
        if ticker != 'dates':
            tickerValueDayOne = holdings[ticker]['shares'] * holdings[ticker]["historicalData"][-1]
            weight = tickerValueDayOne / totalValueDayOne
            holdings[ticker]["weight"] = weight

    return holdings

def findBenchmarkShares(holdings, benchmarks):
    totalValueDayOne = 0
    for ticker in holdings:
        if ticker != 'dates':
            totalValueDayOne += holdings[ticker]['shares'] * holdings[ticker]["historicalData"][0]

    for ticker in benchmarks:
        benchmarks[ticker]['shares'] = (totalValueDayOne * benchmarks[ticker]['weight']) / benchmarks[ticker]['historicalData'][0]

    return benchmarks

def dailyPercentReturnsOnNinetyDay(holdings):
    for ticker in holdings:
        if ticker != 'dates':
            percentDailyReturns = []
            historicData = holdings[ticker]['ninetyDayData']
            for i in range(len(historicData)):
                if i != 0:
                    # Note: ensure that the data is in reverse date order when you import it from yahoo otherwise you will need to switch th i and i-1
                    percentDailyReturns.append((historicData[i - 1] / historicData[i]) - 1)
            holdings[ticker]["percentDailyReturns"] = percentDailyReturns

    return holdings

def dailyPercentReturnsOnHistoricalData(holdings):
    for ticker in holdings:
        if ticker != 'dates':
            percentDailyReturns = []
            historicData = holdings[ticker]['historicalData']
            for i in range(len(historicData)):
                if i != 0:
                    # Note: ensure that the data is in reverse date order when you import it from yahoo otherwise you will need to switch th i and i-1
                    percentDailyReturns.append((historicData[i - 1] / historicData[i]) - 1)
            holdings[ticker]["pdrHistoricalData"] = percentDailyReturns

    return holdings

"""
tester functions:

def checkWeightsAddUp(holdings):
    totalWeight = 0
    for ticker in holdings:
        totalWeight += holdings[ticker]['weight']

    print("The total weight is: " + str(float(totalWeight)))

"""
