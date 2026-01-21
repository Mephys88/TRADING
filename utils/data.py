
import ccxt
import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=60)
def fetch_crypto_data(symbol='BTC/USDT', timeframe='1h', limit=1000):
    """
    Fetch OHLCV data from Bybit via CCXT.
    Default limit increased to 1000 to support decent history.
    """
    try:
        exchange = ccxt.bybit()
        
        # Map timeframes to Bybit standard
        tf_map = {
            '15m': '15',
            '1h': '60',
            '4h': '240',
            '1d': 'D',
            '1D': 'D'
        }
        bybit_tf = tf_map.get(timeframe, timeframe)
        
        ohlcv = exchange.fetch_ohlcv(symbol, bybit_tf, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        st.error(f"Error fetching crypto data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_stock_data(tickers=['^GSPC', '^IXIC']):
    """
    Fetch stock market data (S&P 500, Nasdaq) using yfinance.
    """
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            data[ticker] = hist
        except Exception as e:
            st.error(f"Error fetching stock data for {ticker}: {e}")
    return data

@st.cache_data(ttl=300)
def fetch_dxy_data():
    """
    Fetch US Dollar Index (DXY) data.
    """
    try:
        # DX-Y.NYB is standard on Yahoo Finance, DX=F is futures
        ticker = "DX-Y.NYB" 
        dxy = yf.Ticker(ticker)
        hist = dxy.history(period="1mo", interval="1d")
        if hist.empty:
             # Fallback to Futures if needed
             hist = yf.Ticker("DX=F").history(period="1mo", interval="1d")
        return hist
    except Exception as e:
        st.error(f"Error fetching DXY data: {e}")
        return pd.DataFrame()
