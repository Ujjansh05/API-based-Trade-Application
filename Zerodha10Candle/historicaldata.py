from datetime import datetime, timedelta
import indicators
import pandas as pd
import copy


def transitionpoint(df):
    df = df.drop(df.index[-1])
    # Identify points where candle color changes
    df['Color'] = 'Green'  # Assuming initial color is green
    df.loc[df['close'] < df['open'], 'Color'] = 'Red'

    # Find transition points
    transition_points = df[df['Color'] != df['Color'].shift(1)].index

    # Filter only transition candle data
    transition_data = df.loc[transition_points]
    selected_columns = ['open', 'high', 'low', 'close',	"date","Color"]
   
    if (len(transition_data)==0):
        return [["-", "-", "-", "-", "-", "-"]]
    
   

    return transition_data[selected_columns].tail(1).values.tolist()


def interval_description(interval):
    switch = {
        1: "minute",
        3: "3minute",
        5: "5minute",
        10: "10minute",
        15: "15minute",
        30: "30minute",
        60: "60minute",
        "day": "day"
    }
    
    return switch.get(interval, "5minute")


def formatdataha(df):
    ohlc=[]
    boliger=[]

    df = df.round(2)

    selected_columns = ['HAopen', 'HAhigh', 'HAlow', 'HAclose',	"HAUpperBand","HARollingMean","HAlowerBand"]
    filtered_data_list = df[selected_columns].tail(6).values.tolist()

    for i in filtered_data_list:
        i_copy = copy.copy(i)
        ohlc += i_copy[0:4]
        boliger += i_copy[4:]

    return ohlc+boliger

def formatdata(df):
    ohlc=[]
   
    df = df.round(2)

    selected_columns = ['open', 'high', 'low', 'close']
    filtered_data_list = df[selected_columns].tail(10).values.tolist()

    for i in filtered_data_list:
        i_copy = copy.copy(i)
        ohlc += i_copy[0:4]
        

    return ohlc



def gethistoricaldata(kite,instrument,timeframe):
    now = datetime.now()
    ten_days_ago = now - timedelta(days=18)
    formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
    formatted_15_days_ago = ten_days_ago.strftime('%Y-%m-%d %H:%M:%S')
    test =kite.historical_data(instrument_token=instrument,from_date=formatted_15_days_ago,to_date=formatted_now,interval=interval_description(timeframe))
    data= pd.DataFrame(test)
    #data = indicators.update_heikin_ashi(data)
    #test2 = indicators.calculate_bollinger_bands(data)
    #test2 = indicators.calculate_ha_bollinger_bands(test2)
    
    return  {"normal":formatdata(data)+transitionpoint(data)[0]}

