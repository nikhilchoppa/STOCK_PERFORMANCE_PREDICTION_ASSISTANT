import os
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from pmdarima.arima import auto_arima
from sklearn.metrics import mean_squared_error, mean_absolute_error
import math

ticker_symbol = input("Enter the Stock Symbol:")
tesla_data = yf.Ticker(ticker_symbol)

# history function helps to extract stock information.
# setting period parameter to max to get information for the maximum amount of time.
tsla_data = tesla_data.history(period='max')

tsla_data = tsla_data.asfreq('D')
# Resetting the index
tsla_data.reset_index(inplace=True)

# display the first five rows
tsla_data.head()
tsla_data.set_index("Date", inplace=True)
# Visualize the stock’s daily closing price.
 #plot close price
plt.figure(figsize=(10,6))
plt.grid(True)
plt.xlabel('Date')
plt.ylabel('Close Prices')
plt.plot(tsla_data['Close'])
plt.title('TSLA')
plt.show()

#Distribution of the dataset
df_close = tsla_data['Close']
df_close = df_close.ffill()
df_close.plot(kind='kde')
plt.show()
print("before stationary test")

def test_stationarity(timeseries):
    #Determing rolling statistics
    rolmean = timeseries.rolling(12).mean()
    rolstd = timeseries.rolling(12).std()
    #Plot rolling statistics:
    plt.plot(timeseries, color='blue',label='Original')
    plt.plot(rolmean, color='red', label='Rolling Mean')
    plt.plot(rolstd, color='black', label = 'Rolling Std')
    plt.legend(loc='best')
    plt.title('Rolling Mean and Standard Deviation')
    plt.show(block=False)
    print("Results of dickey fuller test")
    adft = adfuller(timeseries,autolag='AIC')
    # output for dft will give us without defining what the values are.
    #hence we manually write what values does it explains using a for loop
    output = pd.Series(adft[0:4],index=['Test Statistics','p-value','No. of lags used','Number of observations used'])
    for key,values in adft[4].items():
        output['critical value (%s)'%key] =  values
    print(output)
    return adft[0:4], rolmean, rolstd
test_stationarity(df_close)
print("after stationary test")

#To separate the trend and the seasonality from a time series,
# we can decompose the series using the following code.
result = seasonal_decompose(df_close, model='multiplicative', period = 30)

fig = result.plot()
fig.set_size_inches(16, 9)

#if not stationary then eliminate trend
#Eliminate trend
from pylab import rcParams
rcParams['figure.figsize'] = 10, 6
df_log = np.log(df_close)
moving_avg = df_log.rolling(12).mean()
std_dev = df_log.rolling(12).std()
plt.legend(loc ='best')
plt.title('Moving Average')
plt.plot(std_dev, color ="black", label = "Standard Deviation")
plt.plot(moving_avg, color="red", label = "Mean")
plt.legend()
plt.show()

# DEVELOPING ARIMA MODEL :


#split data into train and training set
train_data, test_data = df_log[3:int(len(df_log)*0.9)], df_log[int(len(df_log)*0.9):]
train_data_original_scale = np.exp(train_data)
test_data_original_scale = np.exp(test_data)
plt.figure(figsize=(10,6))
plt.grid(True)
plt.xlabel('Dates')
plt.ylabel('Closing Prices')
plt.plot(df_close, 'green', label='Original data')
plt.plot(train_data_original_scale, 'orange', label='Train data')
plt.plot(test_data_original_scale, 'blue', label='Test data')
plt.legend()

#auto arima
model_autoARIMA = auto_arima(train_data, start_p=0, start_q=0,
                      test='adf',       # use adftest to find optimal 'd'
                      max_p=3, max_q=3, # maximum p and q
                      m=1,              # frequency of series
                      d=None,           # let model determine 'd'
                      seasonal=False,   # No Seasonality
                      start_P=0,
                      D=0,
                      trace=True,
                      error_action='ignore',
                      suppress_warnings=True,
                      stepwise=True)
ft = model_autoARIMA.fit(train_data,disp = -1)
print(model_autoARIMA.summary())
model_autoARIMA.plot_diagnostics(figsize=(15,8))
plt.show()

#Modeling
# Build Model
model = ARIMA(train_data, order = (1,1,2))
fitted = model.fit()
print(fitted.summary())

# Forecast
forecast = fitted.forecast(len(test_data), alpha = 0.05)
# Make as pandas series
fc_series = pd.Series(np.exp(forecast), index=test_data_original_scale.index)
plt.figure(figsize=(10,5), dpi=100)
plt.plot(train_data_original_scale, label='Training Data')
plt.plot(test_data_original_scale, color='blue', label='Actual Stock Price')
plt.plot(fc_series, color='orange', label='Predicted Stock Price')
plt.title(f"{ticker_symbol} Prediction")
plt.xlabel('Time')
plt.ylabel(ticker_symbol)
plt.legend(loc='upper left', fontsize=8)
plt.show()

# EVALUATION :
# report performance
mse = mean_squared_error(test_data, forecast)
print('MSE: '+str(mse))
mae = mean_absolute_error(test_data, forecast)
print('MAE: '+str(mae))
rmse = math.sqrt(mean_squared_error(test_data, forecast))
print('RMSE: '+str(rmse))
mape = np.mean(np.abs(forecast - test_data)/np.abs(test_data))
print('MAPE: '+str(mape))

