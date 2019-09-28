from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone


# Create your models here.

class Portfolio(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    holdings = models.TextField()
    benchmarks = models.TextField()
    start_date = models.TextField()
    end_date = models.TextField()
    sector = models.TextField()
    #last_updated = models.TextField()

    def get_holdings_dict(self):
        holdings_dict = eval(self.data)
        return holdings_dict

    def get_benchmarks_dict(self):
        benchmarks_dict = eval(self.data)
        return get_benchmark_dict

"""
class Holdings(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.TextField()

    def getDict(self):
        holdingsDict = eval(self.data)
        return holdingsDict

    def element(self, key):
        dataDict = eval(self.data)
        element = str(key) + ": " + str(dataDict[key]) + " shares"
        return element

    def toArray(self):
        holdingsDict = eval(self.data)
        returnArray = [self.element(key) for key in holdingsDict]
        return returnArray

class Benchmark(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.TextField()

    def element(self, key):
        dataDict = eval(self.data)
        element = str(key) + ": " + str(dataDict[key]) + " (weight)"
        return element

    def toArray(self):
        holdingsDict = eval(self.data)
        returnArray = [self.element(key) for key in holdingsDict]
        return returnArray
"""
