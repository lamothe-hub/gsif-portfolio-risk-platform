"""gsif URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from dashboards import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.loading, name = 'loading'),
    path('dashboard', views.landing, name = 'landing'),
    path('login/', views.login, name = 'login'),
    path('logged-in/', views.logged_in, name = 'logged_in'),
    path('portfolio/', views.portfolio, name = 'portfolio'),
    path('portfolio-select/', views.portfolio_select, name = 'portfolio_select'),
    path('add-user/', views.add_user, name = 'add_user'),
    path('process-new-user/', views.process_new_user, name = 'process_new_user'),
    path('test/', views.test, name = 'test'),
    path('tev/', views.tev, name = 'tev'),
    path('tev-dates/', views.tev_dates, name = 'tev_dates'),
    path('test_chart/', views.test_chart, name = 'test_chart'),
    path('edit-portfolio/', views.edit_portfolio, name = 'edit_portfolio'),
    path('add-holding/', views.add_holding, name = 'add_holding'),
    path('add-benchmark/', views.add_benchmark, name = 'add_benchmark'),
    path('delete-holdings/', views.delete_holdings, name = 'delete_holdings'),
    path('delete-benchmarks/', views.delete_benchmarks, name = 'delete_benchmarks'),
    path('test-landing/', views.test_landing, name = 'test_landing'),
    path('loading/', views.loading, name = 'loading'),
    path('optimization/', views.optimization, name = 'optimization'),
    path('chart/', views.chart, name = 'chart'),
    path('trade-cycle', views.change_trade_cycle, name='change_trade_cycle'),
    path('update-date', views.update_trade_date, name='update_trade_date'),
    path('table', views.table, name='table'),







]
