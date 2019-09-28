import quandl
import preprocess, dataAccess, calculate
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pprint
import datetime
import json

import fix_yahoo_finance


holdings, benchmarks = preprocess.setup()
tev = calculate.trackingErrorVolatility(holdings, benchmarks)
pdr = calculate.cumulative_returns_no_shares(holdings, benchmarks)
tevs = calculate.tev_plot_array(holdings, tev)


print(pdr)
# plot the percent excess returns

#plt.plot(tevs)
plt.plot(pdr)
plt.ylabel('cumulative returns')
plt.show()





exit()