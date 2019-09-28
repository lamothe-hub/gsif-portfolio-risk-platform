import datetime
from pandas_datareader import data as pdr
import queue
import threading
from pprint import pprint
def pullHistoricalData(holdings, benchmarks, start_date, end_date):

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

            #print("About to make call with ninety start: " + str(ninety_day_start))
            try:
                yahoo_data = pdr.get_data_yahoo(ticker, ninety_day_start, end_date)
                #print("Received yahoo_data for " + str(ticker))
            except:
                print("ensure_90_days has failed for: " + str(ticker))
            difference = 90 - len(list(yahoo_data['Close'][:start_date]))
            #print("The current difference is: " + str(difference))
            if difference > 0:
                ninety_day_start = ninety_day_start - datetime.timedelta(days=difference)
                #print("About to call function with new ninety start date of: " + str(ninety_day_start))
                yahoo_data = ensure_90_days(ticker, ninety_day_start, start_date, end_date)
            return yahoo_data

        while True:
            #print("Queue length: " + str(q.qsize()))
            item = q.get()
            if item is None:
                break
            ticker, ninety_day_start, start_date, end_date = item
            start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            ninety_day_start = start - datetime.timedelta(days=129)
            if True:
                if ticker not in done:
                    #print("ticker: " + ticker)
                    #print("done: " + str(done))
                    try:
                        yahoo_data = ensure_90_days(ticker, ninety_day_start, start_date, end_date)
                    except:
                        print("FAILURE POINT A")
                    try:
                        data[ticker] = {}
                        data[ticker]['ninetyDayData'] = list(yahoo_data['Close'][:start_date])
                        data[ticker]['historicalData'] = list(yahoo_data['Close'][start_date:])
                        #print("Completed " + str(item))
                        done.add(ticker)
                        #print("appending " + ticker + "to done")
                    except:
                        print("FAILURE POINT B")

                else:
                    print("Already completed: " + str(ticker) + ". Rejecting.")

            #print(yahoo_data['Close'][:start_date])

            q.task_done()


    requests = []
    start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    ninety_day_start = start - datetime.timedelta(days=129)
    for ticker in holdings.keys():
        requests.append((ticker, ninety_day_start, start_date, end_date))
    for ticker in benchmarks.keys():
        if ticker not in holdings.keys():
            requests.append((ticker, ninety_day_start, start_date, end_date))
    #print("requests: ")
    #pprint(requests)
    q = queue.Queue()
    done = set()
    data = {}
    threads = []

    thread_count = len(requests)
    #print("Creating " + str(thread_count) + " threads...")
    for i in range(thread_count):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)
        #print("i: " + str(i))

    for item in requests:
        #print("item: " + str(item))
        q.put(item)

    q.join()
    #print("q has joined.")
    for i in range(len(threads)):
        q.put(None)
    for t in threads:
        t.join


    return assign_data_to_ticker(holdings, benchmarks, data)

def printDates():

    filename = 'files/AMN.csv'
    file = open(filename, 'r')
    dates = []
    for line in file:
        lineArray = line.split(',')
        dates.append(lineArray[0])

    print(dates)

def getDates():
    filename = 'files/AMN.csv'
    file = open(filename, 'r')
    dates = []
    for line in file:
        lineArray = line.split(',')
        dates.append(lineArray[0])
    return dates

def pullImpliedVols(connection, startDate, endDate):
    dummyArray = [1, 2, 3]
