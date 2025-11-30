import pandas


def update_heikin_ashi(df):
    df['HAopen'] = round((df['open'].shift(1) + df['close'].shift(1)) / 2,2)
    df['HAclose'] = round((df['open'] + df['high'] + df['low'] + df['close']) / 4,2)
    df['HAhigh'] = round(df[['high', 'open', 'close']].max(axis=1),2)
    df['HAlow'] = round(df[['low', 'open', 'close']].min(axis=1),2)

    return df

def calculate_ha_bollinger_bands(df, window=10, num_std_dev=2):
    # Calculate rolling mean and standard deviation
    df['HARollingMean'] = df['HAclose'].rolling(window=window).mean()
    df['HAUpperBand'] = df['HARollingMean'] + (df['HAclose'].rolling(window=window).std() * num_std_dev)
    df['HAlowerBand'] = df['HARollingMean'] - (df['HAclose'].rolling(window=window).std() * num_std_dev)
    return df



def calculate_bollinger_bands(df, window=10, num_std_dev=2):
    # Calculate rolling mean and standard deviation
    df['Rolling Mean'] = df['close'].rolling(window=window).mean()
    df['Upper Band'] = df['Rolling Mean'] + (df['close'].rolling(window=window).std() * num_std_dev) 
    df['lower Band'] = df['Rolling Mean'] - (df['close'].rolling(window=window).std() * num_std_dev)
    return df


def calculate_stochastic_momentum(df, k_period=6, d_period=3, slowing=3, tma_period=3):
    # Calculate the raw Stochastic Oscillator %K
    df['lowest_low'] = df['low'].rolling(window=k_period).min()
    df['highest_high'] = df['high'].rolling(window=k_period).max()
    df['%K'] = 100 * ((df['close'] - df['lowest_low']) / (df['highest_high'] - df['lowest_low']))

    # Calculate the Stochastic Oscillator %D using an exponential moving average (EMA)
    df['%D'] = df['%K'].ewm(span=d_period).mean()

    # Apply triple smoothing using the TMA (Triangular Moving Average)
    df['%K_TMA'] = df['%K'].rolling(window=tma_period).mean()
    df['%D_TMA'] = df['%D'].rolling(window=tma_period).mean()
    return df
