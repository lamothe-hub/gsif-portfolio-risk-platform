from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from datetime import datetime, timedelta
from django.utils import timezone
from dashboards.models import Portfolio
from dashboards.test_package import demo
from dashboards.calculations import preprocess, calculate, clean_preprocess
from pprint import pprint
import random
import datetime
import time
import json
import ast
import csv
# Create your views here.

def chart(request):
    portfolio = Portfolio.objects.all()
    for sector in portfolio:
        holdings = ast.literal_eval(sector.holdings)
    return render(request, 'dashboards/chart.html')

def test(request):
    returns = calculate.absoluteReturnsForAllMasterSectors()
    request.session['returns'] = returns
    return render(request, 'dashboards/test.html')

def test_landing(request):
    holdings, benchmarks = preprocess.setup('energy')
    holdings_data = calculate.absoluteReturns(holdings)
    # pdr = calculate.pdr_against_benchmark_by_shares(holdings, benchmarks)
    request.session['holdings_data'] = holdings_data
    benchmarks_data = calculate.absoluteReturns(benchmarks)
    request.session['benchmarks_data'] = benchmarks_data

    return render(request, 'dashboards/test_landing.html')

def test_chart(request):
    return render(request, 'dashboards/test_chart.html')

def tev_dates(request):
    return render(request, 'dashboards/tev_dates.html', {'userAuthenticated': request.user.is_authenticated})

def tev(request):
    #print("Inside tev")
    def setup_sector(sector, start_date, end_date):
        #print("Inside setup_sector")
        holdings, benchmarks = clean_preprocess.tev_setup(sector, start_date, end_date)
        #print("After tev_setup")
        #pprint(holdings)
        pdr = calculate.pdr_against_benchmark_by_shares(holdings, benchmarks)
        tev = calculate.trackingErrorVolatility(holdings, benchmarks)
        tevs = calculate.tev_plot_array(holdings, tev)
        negative_tevs = [(tev * -1) for tev in tevs]
        x_axis = [i for i in range(len(pdr))]
        request.session['tev_start_date'] = str(start_date)
        request.session['tev_x'] = x_axis
        request.session['tev_tev'] = round(tev, 6)
        request.session['tev_pdr'] = pdr
        request.session['tev_tevs'] = tevs
        request.session['tev_negative_tevs'] = negative_tevs

    try:
        sector = request.GET['sector']
    except:
        return render(request, 'dashboards/tev_dates.html', {'userAuthenticated': request.user.is_authenticated, 'message':['You must select a sector']})

    start_date = request.GET['start_date']
    end_date = request.GET['end_date']

    #try:
    setup_sector(sector, start_date, end_date)
    return render(request, 'dashboards/tev.html', {'userAuthenticated': request.user.is_authenticated, 'sector':sector.capitalize(),})
    #except:
    #message = ['Could not pull data from that time period. Please make sure you are using valid dates.', '-------','Make sure the sector portfolio is valid and contains valid ticker symbols for both holdings and benchmarks']
    #return render(request, 'dashboards/tev_dates.html', {'userAuthenticated': request.user.is_authenticated, 'message':message})


def landing(request):
    message, holdings, benchmarks = '','',''
    calculate.absoluteReturnsForAllMasterSectors(request) #calculates returns and sets session variables for chart.
    print("Inside landing _-----_----_")
    print(request.session['absolute_x'])
    print(request.session['dates_axis'])
    print(request.session['test_letters'])
    return render(request, 'dashboards/landing.html', {'userAuthenticated':request.user.is_authenticated, 'message':message, 'holdings':holdings, 'benchmarks':benchmarks})

def add_user(request):
    return render(request, 'dashboards/add_user.html')

def process_new_user(request):
    inputUsername = request.GET['username']
    inputPassword = request.GET['password']
    user = User.objects.create_user(inputUsername, '', inputPassword)
    user.save()
    for sector in ['energy', 'tech', 'healthcare']:
        portfolio = Portfolio.objects.create(
            owner = user,
            holdings = '{}',
            benchmarks = '{}',
            start_date = '',
            end_date = '',
            sector = sector,
        )
        portfolio.save()
        """
            owner = models.ForeignKey(User, on_delete=models.CASCADE)
            holdings = models.TextField()
            benchmarks = models.TextField()
            start_date = models.TextField()
            end_date = models.TextField()
            sector = models.TextField()
        """
    return landing(request)

def login(request):
    if request.user.is_authenticated:
        auth_logout(request)
        return redirect('loading')
    return render(request, 'dashboards/login.html', {'message': ''})

def logged_in(request):
    inputUsername = request.GET['username']
    inputPassword = request.GET['password']
    user = authenticate(username=inputUsername, password=inputPassword)
    if user is not None:
        auth_login(request, user)
        return redirect('loading')
    else:
        return render(request, 'dashboards/login.html', {'message': 'That is not a valid username/password'})

def portfolio_select(request):
    master_user = User.objects.get(username='master')
    current_portfolio = Portfolio.objects.get(owner=master_user, sector='energy')
    start_date = current_portfolio.start_date
    return render(request, 'dashboards/portfolio_select.html', {'userAuthenticated':request.user.is_authenticated, 'start_date':start_date})


def edit_portfolio(request):
    # edit the portfolio then call portfolio again
    return portfolio(request, '')



def add_holding(request):
    # TODO: make sure that the ticker is valid and check that the number is a valid int.
    try:
        ticker = request.GET['ticker']
        shares = request.GET['shares']
        price = request.GET['price']
    except:
        ticker = ''
        shares = ''
        price = ''
        return redirect('portfolio_select')
    if not shares.isdigit():
        return portfolio(request, 'Please enter a positive integer for share count.')

    def check_valid_ticker(ticker):
        filename = 'dashboards/static/dashboards/tickers.csv'
        tickers = []
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row != []:
                    tickers.append(row[0])
        if ticker not in tickers:
            return False
        else:
            return True


    if not check_valid_ticker(ticker):
        return portfolio(request, 'Please enter a valid ticker symbol.')


    sector = request.GET['sector']
    try:
        sector_portfolio = Portfolio.objects.get(sector=sector, owner=request.user)
    except:
        print("Portfolio not found for sector: " + sector + ", user: " + str(request.user.username))
        return landing(request)
    try:
        new_holdings = ast.literal_eval(sector_portfolio.holdings)
        new_holdings[ticker] = {}
        new_holdings[ticker]['shares'] = shares
        new_holdings[ticker]['price'] = price
        sector_portfolio.holdings = json.dumps(new_holdings)
        sector_portfolio.end_date = '2000-01-01'
        sector_portfolio.save()
        return redirect(portfolio)
    except:
        print("something wrong in second try block, ast.literal_eval might be processing an invalid string in db")
        return landing(request)

def delete_holdings(request):
    current_sector = request.session['sector']
    sector_portfolio = Portfolio.objects.get(owner=request.user, sector=current_sector)
    sector_portfolio.holdings = '{}'
    sector_portfolio.save()
    return redirect(portfolio)

def add_benchmark(request):
    # TODO: make sure that the ticker is valid and check that the number is a valid int.
    ticker = request.GET['ticker']
    weight = request.GET['weight']
    
    if float(weight) > 1 or float(weight) < 0:
        return portfolio(request, '', 'Weights should be a number between 0 and 1')

    def check_valid_ticker(ticker):
        filename = 'dashboards/static/dashboards/tickers.csv'
        tickers = []
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row != []:
                    tickers.append(row[0])
        if ticker not in tickers:
            return False
        else:
            return True


    if not check_valid_ticker(ticker):
        return portfolio(request, '', 'Please enter a valid ticker symbol.')


    sector = request.GET['sector']
    try:
        sector_portfolio = Portfolio.objects.get(sector=sector, owner=request.user)
    except:
        print("Portfolio not found for sector: " + sector + ", user: " + str(request.user.username))
        return landing(request)
    try:
        new_benchmarks = ast.literal_eval(sector_portfolio.benchmarks)
        new_benchmarks[ticker] = {}
        new_benchmarks[ticker]['weight'] = weight
        sector_portfolio.benchmarks = json.dumps(new_benchmarks)
        sector_portfolio.end_date = '2000-01-01'
        sector_portfolio.save()
        return redirect(portfolio)
    except:
        print("something wrong in second try block, ast.literal_eval might be processing an invalid string in db")
        return landing(request)

def delete_benchmarks(request):
    current_sector = request.session['sector']
    user_portfolio = Portfolio.objects.get(owner=request.user, sector=current_sector)
    user_portfolio.benchmarks = '{}'
    user_portfolio.save()
    return redirect(portfolio)

def portfolio(request, holdings_message = '', benchmarks_message = ''):

    def retrieve_current_portfolio(request, sector):
        # this will retrieve the current portfolio of the user that is logged in for the sector they selected
        # for now, we will assume that master is the only one that will be logged in.
        holdings, benchmarks, start_date, end_date = '','','',''
        try:
            portfolio = Portfolio.objects.get(sector=sector, owner=request.user)
            holdings = portfolio.holdings
            benchmarks = portfolio.benchmarks
            start_date = portfolio.start_date
            end_date = portfolio.end_date
            return True, holdings, benchmarks, start_date, end_date
        except:
            print("Did not find a(n) " + sector + " for " + str(request.user.username))
            return False, '','','',''

    def prepare_data(portfolio_exists, sector, holdings, benchmarks, start_date, end_date, holdings_message, benchmarks_message):
        print("VIEWS: PREPARE_DATA: holdings: " + str(holdings))
        dict_holdings = ast.literal_eval(holdings)
        dict_benchmarks = ast.literal_eval(benchmarks)
        data_holdings = []
        for h in dict_holdings.keys():
            if h != 'dates':
                data_holdings.append(h + ": " + str(dict_holdings[h]['shares']))
        data_benchmarks = []
        for b in dict_benchmarks.keys():
            data_benchmarks.append(b + ": " + str(dict_benchmarks[b]['weight']))
        data = {
            'portfolio_exists':portfolio_exists,
            'holdings':data_holdings,
            'benchmarks':data_benchmarks,
            'start_date':start_date,
            'end_date':end_date,
            'sector':sector,
            'sector_capitalized':sector.capitalize(),
            'holdings_message':holdings_message,
            'benchmarks_message':benchmarks_message,
            'userAuthenticated':request.user.is_authenticated
        }
        return data

    sector = ''
    try:
        sector = request.GET['sector']
        request.session['sector'] = sector
    except:
        print("sector was not found in form data. Pulling from session...")
        if 'sector' in request.session:
            sector = request.session['sector']
        else:
            print("sector was not found in form data OR session data.")

    portfolio_exists, holdings, benchmarks, start_date, end_date = retrieve_current_portfolio(request, sector)
    data = prepare_data(portfolio_exists, sector, holdings, benchmarks, start_date, end_date, holdings_message,benchmarks_message)
    return render(request, 'dashboards/portfolio.html', data)

def loading(request):
    return render(request, 'dashboards/loading.html', {'userAuthenticated':request.user.is_authenticated})

def optimization(request):
    return render(request, 'dashboards/optimization.html', {'userAuthenticated': request.user.is_authenticated})

def change_trade_cycle(request):
    return render(request, 'dashboards/change_trade_cycle.html', {'userAuthenticated': request.user.is_authenticated})

def update_trade_date(request):
    portfolios = Portfolio.objects.all()
    new_date = str(request.GET['start_date'])
    #print("New date: " + str(new_date))
    for portfolio in portfolios:
        #print("updating start_date for " + str(portfolio.sector))
        portfolio.start_date = new_date
        portfolio.end_date = new_date
        portfolio.save()
    return render(request, 'dashboards/loading.html', {'userAuthenticated': request.user.is_authenticated})

def table(request):
    portfolios = Portfolio.objects.all()
    sectors = []
    data = {}
    for portfolio in portfolios:
        sector = portfolio.sector
        tickers = []
        shares = []
        original_values = []
        current_values = []
        percent_changes = []
        data[portfolio.sector] = {}
        holdings = ast.literal_eval(portfolio.holdings)
        for ticker in holdings.keys():
            if ticker != 'dates':
                tickers.append(ticker)
                shares.append(int(holdings[ticker]['shares']))
                original = holdings[ticker]['historicalData'][0] * holdings[ticker]['shares']
                original_values.append(int(holdings[ticker]['historicalData'][0] * holdings[ticker]['shares'] + .5))
                current = holdings[ticker]['historicalData'][-1] * holdings[ticker]['shares']
                current_values.append(int(holdings[ticker]['historicalData'][-1] * holdings[ticker]['shares'] + .5))
                percent = ((current - original) / original ) * 100
                percent_changes.append(str('%.2f' % percent) + '%')
        data[sector]['tickers'] = tickers
        data[sector]['shares'] = shares
        data[sector]['originial_values'] = original_values
        data[sector]['current_values'] = current_values
        data[sector]['percent_changes'] = percent_changes

    data_package = {
        'energy_tickers':data['energy']['tickers'],
        'energy_shares':data['energy']['shares'],
        'energy_original_values':data['energy']['originial_values'],
        'energy_current_values':data['energy']['current_values'],
        'energy_percent_changes':data['energy']['percent_changes'],


        'tech_tickers':data['tech']['tickers'],
        'tech_shares':data['tech']['shares'],
        'tech_original_values':data['tech']['originial_values'],
        'tech_current_values':data['tech']['current_values'],
        'tech_percent_changes':data['tech']['percent_changes'],

        'healthcare_tickers':data['healthcare']['tickers'],
        'healthcare_shares':data['healthcare']['shares'],
        'healthcare_original_values':data['healthcare']['originial_values'],
        'healthcare_current_values':data['healthcare']['current_values'],
        'healthcare_percent_changes':data['healthcare']['percent_changes'],

        'financials_tickers':data['financials']['tickers'],
        'financials_shares':data['financials']['shares'],
        'financials_original_values':data['financials']['originial_values'],
        'financials_current_values':data['financials']['current_values'],
        'financials_percent_changes':data['financials']['percent_changes'],

        'consumers_tickers':data['consumers']['tickers'],
        'consumers_shares':data['consumers']['shares'],
        'consumers_original_values':data['consumers']['originial_values'],
        'consumers_current_values':data['consumers']['current_values'],
        'consumers_percent_changes':data['consumers']['percent_changes'],

        'industrials_tickers':data['industrials']['tickers'],
        'industrials_shares':data['industrials']['shares'],
        'industrials_original_values':data['industrials']['originial_values'],
        'industrials_current_values':data['industrials']['current_values'],
        'industrials_percent_changes':data['industrials']['percent_changes'],

        'userAuthenticated': request.user.is_authenticated
    }

    #pprint(data)
    return render(request, 'dashboards/table.html', data_package)
