import pandas as pd
from datetime import datetime
import logging
from data_fetcher import fetch_data_for_strategy, get_all_symbols
from database import add_entry, get_setting, set_setting
from notifier import send_bulk_email_alert
import os
import time

logger = logging.getLogger(__name__)

stop_scan_flag = False
is_scanning = False

def load_nifty500_symbols():
    APP_DIR = os.path.expanduser('~/.multi_strategy_scanner')
    file_path = os.path.join(APP_DIR, 'nifty500.csv')
    
    try:
        import requests
        import io
        logger.info("Downloading live Nifty 500 list from NSE...")
        res = requests.get('https://archives.nseindia.com/content/indices/ind_nifty500list.csv', headers={'User-Agent': 'Mozilla/5.0'})
        res.raise_for_status()
        df = pd.read_csv(io.StringIO(res.text))
        os.makedirs(APP_DIR, exist_ok=True)
        df.to_csv(file_path, index=False)
        if 'Symbol' in df.columns: return df['Symbol'].tolist()
        elif 'SYMBOL' in df.columns: return df['SYMBOL'].tolist()
        else: return df.iloc[:, 2].tolist()
    except Exception as e:
        logger.warning(f"Failed to download from NSE ({e}). Trying to use cached CSV.")
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                if 'Symbol' in df.columns: return df['Symbol'].tolist()
                elif 'SYMBOL' in df.columns: return df['SYMBOL'].tolist()
                else: return df.iloc[:, 0].tolist()
            except:
                pass
        return ["TCS", "RELIANCE", "INFY"]

def evaluate_52w(df):
    # Need at least 53 weekly bars: 52 previous (1 year) + 1 current
    if len(df) < 53:
        return False, None, None
    current = df.iloc[-1]
    prev_week = df.iloc[-2]          # Last fully-closed weekly candle
    prev_52 = df.iloc[-53:-1]        # The 52 candles before the current one

    # A true 52-week high breakout: current CLOSE exceeds the highest
    # CLOSING price of the previous 52 weeks (not the wick highs).
    max_close_52w = prev_52['close'].max()

    if current['close'] > max_close_52w:
        entry = current['close']
        # SL = previous week's LOW (a confirmed, fully-closed candle).
        # Avoids using an incomplete mid-week low from the current candle.
        sl = prev_week['low']
        risk = entry - sl
        if risk <= 0: return False, None, None
        tp = entry + (3 * risk)
        return True, sl, tp
    return False, None, None

def evaluate_ath(df):
    if len(df) < 2:
        return False, None, None
    current = df.iloc[-1]
    prev_all = df.iloc[:-1]
    max_high = prev_all['high'].max()
    if pd.isna(max_high): return False, None, None
    if current['close'] > max_high:
        entry = current['close']
        sl = current['low']
        risk = entry - sl
        if risk <= 0: return False, None, None
        tp = entry + (3 * risk)
        return True, sl, tp
    return False, None, None

def evaluate_5m(df):
    if len(df) < 6:
        return False, None, None
    last_6 = df.tail(6)
    c1 = last_6.iloc[0]
    c2 = last_6.iloc[1]
    c3 = last_6.iloc[2]
    c4 = last_6.iloc[3]
    c5 = last_6.iloc[4]
    c6 = last_6.iloc[5]
    
    if (c1['close'] < c1['open'] and 
        c2['close'] > c2['open'] and 
        c3['close'] > c3['open'] and 
        c4['close'] > c4['open'] and 
        c5['close'] > c5['open'] and 
        c6['close'] > c6['open']):
        entry = c6['close']
        sl = c6['low']
        risk = entry - sl
        if risk <= 0: return False, None, None
        tp = entry + (3 * risk)
        return True, sl, tp
    return False, None, None

def run_scanner(strategy_id):
    global stop_scan_flag, is_scanning
    if is_scanning:
        logger.warning("Scan is already in progress.")
        return
        
    stop_scan_flag = False
    is_scanning = True

    try:
        _run_scanner_core(strategy_id)
    finally:
        is_scanning = False

def _run_scanner_core(strategy_id):
    global stop_scan_flag
    
    scan_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Starting Scan for {strategy_id}...")
        
    universe = get_setting('UNIVERSE', "Nifty 500")
    if universe == "Nifty 500":
        base_symbols = load_nifty500_symbols()
        symbols = [f"{sym}.NS" for sym in base_symbols]
    else:
        symbols = get_all_symbols(universe)
        
    max_price_setting = get_setting('MAX_STOCK_PRICE', "")
    max_price = float(max_price_setting) if max_price_setting else None
    
    vol_enabled_monthly = get_setting('ENABLE_VOLUME_FILTER', "false").lower() == "true"
    min_vol_monthly_setting = get_setting('MIN_VOLUME', "")
    min_vol_monthly = float(min_vol_monthly_setting) if min_vol_monthly_setting else None
    
    vol_enabled_weekly = get_setting('ENABLE_WEEKLY_VOLUME_FILTER', "false").lower() == "true"
    min_vol_weekly_setting = get_setting('MIN_WEEKLY_VOLUME', "")
    min_vol_weekly = float(min_vol_weekly_setting) if min_vol_weekly_setting else None
    
    triggered_symbols = []
    
    delay = 0.3
    for symbol in symbols:
        if stop_scan_flag:
            break

        logger.info(f"Scanning {symbol} using {strategy_id}...")
        df = fetch_data_for_strategy(symbol, strategy_id)
        
        if df is None or df.empty:
            continue
            
        if strategy_id == '5m':
            if vol_enabled_monthly and min_vol_monthly is not None:
                last_10 = df.tail(10)
                if len(last_10) > 0:
                    avg_vol = last_10['volume'].mean()
                    if avg_vol <= min_vol_monthly:
                        continue
        elif strategy_id in ['52w', 'ath']:
            if vol_enabled_weekly and min_vol_weekly is not None:
                last_10 = df.tail(10)
                if len(last_10) > 0:
                    avg_vol = last_10['volume'].mean()
                    if avg_vol <= min_vol_weekly:
                        continue
        
        if strategy_id == '52w':
            is_triggered, sl, tp = evaluate_52w(df)
        elif strategy_id == 'ath':
            is_triggered, sl, tp = evaluate_ath(df)
        elif strategy_id == '5m':
            is_triggered, sl, tp = evaluate_5m(df)
        else:
            is_triggered = False
        
        if is_triggered:
            entry_price = df.iloc[-1]['close']
            risk_pct = ((entry_price - sl) / entry_price) * 100
            reward_pct = ((tp - entry_price) / entry_price) * 100
            
            if max_price is not None:
                if risk_pct > 25.9:
                    allowed_capital = max_price * 0.50
                    risk_status = "High Risk High Reward"
                    capital_usage = "50% of Allocated Capital"
                else:
                    allowed_capital = max_price
                    risk_status = "Low Risk High Reward"
                    capital_usage = "100% of Allocated Capital"
                    
                if entry_price > allowed_capital:
                    continue
            else:
                if risk_pct > 25.9:
                    risk_status = "High Risk High Reward"
                    capital_usage = "50% of Allocated Capital"
                else:
                    risk_status = "Low Risk High Reward"
                    capital_usage = "100% of Allocated Capital"
            
            logger.info(f"*** TRIGGER: {symbol} at {entry_price} ***")
            add_entry(symbol, scan_timestamp, entry_price, sl, tp, risk_status, capital_usage, strategy_id)
            
            triggered_symbols.append({
                'symbol': symbol, 'entry_price': entry_price, 'sl': sl, 'tp': tp,
                'risk_pct': risk_pct, 'reward_pct': reward_pct,
                'risk_status': risk_status, 'capital_usage': capital_usage
            })
                
        time.sleep(delay)
        
    if triggered_symbols:
        send_bulk_email_alert(triggered_symbols, strategy_id)

    set_setting("LAST_SCAN_TIME", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
