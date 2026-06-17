import pandas as pd
import logging
from database import get_setting, set_setting
import requests
import yfinance as yf
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_symbols(universe="Nifty 500"):
    symbols = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    if universe == "Nifty 50":
        try:
            url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                df = pd.read_csv(io.StringIO(res.text))
                base_symbols = df['Symbol'].dropna().astype(str).tolist()
                nse_symbols = [f"{s}.NS" for s in base_symbols if s]
                symbols.extend(list(set(nse_symbols)))
        except Exception as e:
            logger.error(f"Failed to fetch Nifty 50: {e}")
            
    elif universe == "Nifty 500":
        try:
            url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                df = pd.read_csv(io.StringIO(res.text))
                base_symbols = df['Symbol'].dropna().astype(str).tolist()
                nse_symbols = [f"{s}.NS" for s in base_symbols if s]
                symbols.extend(list(set(nse_symbols)))
        except Exception as e:
            logger.error(f"Failed to fetch Nifty 500: {e}")
            
    if universe in ["All NSE", "All NSE & BSE"]:
        try:
            url = "https://public.fyers.in/sym_details/NSE_CM.csv"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                df = pd.read_csv(io.StringIO(res.text), header=None, low_memory=False)
                base_symbols = df[13].dropna().astype(str).tolist()
                cleaned_symbols = [s.replace('-EQ', '').replace('-BE', '') for s in base_symbols]
                nse_symbols = [f"{s}.NS" for s in cleaned_symbols if s]
                symbols.extend(list(set(nse_symbols)))
        except Exception as e:
            logger.error(f"Failed to fetch NSE master: {e}")
            
    if universe in ["All BSE", "All NSE & BSE"]:
        try:
            url = "https://public.fyers.in/sym_details/BSE_CM.csv"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                df = pd.read_csv(io.StringIO(res.text), header=None, low_memory=False)
                base_symbols = df[13].dropna().astype(str).tolist()
                bse_symbols = [f"{s}.BO" for s in base_symbols if s]
                symbols.extend(list(set(bse_symbols)))
        except Exception as e:
            logger.error(f"Failed to fetch BSE master: {e}")
            
    return symbols

def fetch_data_for_strategy(symbol, strategy_id):
    """
    Fetches required historical data based on the strategy timeframe and length.
    Expected symbol format: 'RELIANCE.NS'
    """
    try:
        if strategy_id == "52w":
            # Need at least 52 weeks (1 year) + current week. Fetch 2 years to be safe.
            df = yf.download(tickers=symbol, period="2y", interval="1wk", progress=False, auto_adjust=False)
        elif strategy_id == "ath":
            # Need maximum data to find all-time high
            df = yf.download(tickers=symbol, period="max", interval="1wk", progress=False, auto_adjust=False)
        elif strategy_id == "5m":
            # Need at least 6 months of data. 2 years is safe.
            df = yf.download(tickers=symbol, period="2y", interval="1mo", progress=False, auto_adjust=False)
        else:
            return None
        
        if df.empty:
            return pd.DataFrame()
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.columns = [col.lower() for col in df.columns]
        df.index.name = 'date'
        
        # Drop rows with NaN in OHLCV which might happen on some incomplete weeks/months
        df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
        return df
    except Exception as e:
        logger.error(f"Exception fetching data for {symbol}: {str(e)}")
        return None
