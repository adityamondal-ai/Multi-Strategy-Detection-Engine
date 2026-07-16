import pandas as pd
import logging
import re
from database import get_setting, set_setting
import requests
import yfinance as yf
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: find which column in a headerless DataFrame contains NSE tickers
# ---------------------------------------------------------------------------
def _find_nse_ticker_col(df):
    """
    Find the column index that contains NSE ticker symbols like RELIANCE, TCS.
    Checks both raw values and values with '-EQ' / '-BE' suffixes stripped.
    """
    known = {'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'WIPRO', 'SBIN'}
    suffix_pat = re.compile(r'-(EQ|BE|SM|BL|IL|N[0-9]+)$')
    for col in df.columns:
        vals = df[col].dropna().astype(str).tolist()[:300]
        raw_set = set(vals)
        cleaned_set = {suffix_pat.sub('', v) for v in vals}
        if known & raw_set or known & cleaned_set:
            return col
    return None


# ---------------------------------------------------------------------------
# Helper: find which column contains BSE numeric scrip codes (4-7 digit ints)
# ---------------------------------------------------------------------------
def _find_bse_scrip_col(df):
    """
    Find the column that contains numeric BSE scrip codes like 500325.
    Returns the column label where the majority of sampled rows are 4-7 digit ints.
    From live inspection, the Fyers BSE_CM.csv has scrip codes in column 12.
    We verify dynamically and fall back to brute-force search.
    """
    # First try known position (col 12 confirmed from Fyers BSE_CM.csv structure)
    if 12 in df.columns:
        sample = df[12].dropna().astype(str).tolist()[:100]
        score = sum(1 for v in sample if v.isdigit() and 4 <= len(v) <= 7)
        if score > 30:
            return 12
    # Brute-force search as fallback
    best_col, best_score = None, 0
    for col in df.columns:
        vals = df[col].dropna().astype(str).tolist()[:150]
        score = sum(1 for v in vals if v.isdigit() and 4 <= len(v) <= 7)
        if score > best_score:
            best_score, best_col = score, col
    return best_col if best_score > 10 else None


# ---------------------------------------------------------------------------
# Main symbol-list function
# ---------------------------------------------------------------------------
def get_all_symbols(universe="Nifty 500"):
    symbols = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # -----------------------------------------------------------------------
    # Nifty 50
    # -----------------------------------------------------------------------
    if universe == "Nifty 50":
        try:
            url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            df = pd.read_csv(io.StringIO(res.text))
            base = df['Symbol'].dropna().astype(str).tolist()
            syms = [f"{s}.NS" for s in base if s and s.lower() != 'nan']
            symbols.extend(list(set(syms)))
            logger.info(f"Fetched {len(syms)} Nifty 50 symbols")
        except Exception as e:
            logger.error(f"Failed to fetch Nifty 50: {e}")

    # -----------------------------------------------------------------------
    # Nifty 500
    # -----------------------------------------------------------------------
    elif universe == "Nifty 500":
        try:
            url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            df = pd.read_csv(io.StringIO(res.text))
            base = df['Symbol'].dropna().astype(str).tolist()
            syms = [f"{s}.NS" for s in base if s and s.lower() != 'nan']
            symbols.extend(list(set(syms)))
            logger.info(f"Fetched {len(syms)} Nifty 500 symbols")
        except Exception as e:
            logger.error(f"Failed to fetch Nifty 500: {e}")

    # -----------------------------------------------------------------------
    # All NSE  (used for both "All NSE" and "All NSE & BSE")
    # Primary  : NSE official EQUITY_L.csv  → SYMBOL column → .NS
    # Fallback : Fyers NSE_CM.csv with dynamic column detection
    # -----------------------------------------------------------------------
    if universe in ["All NSE", "All NSE & BSE"]:
        fetched = False

        # — Primary —
        try:
            logger.info("Fetching All NSE from NSE EQUITY_L.csv …")
            url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            res = requests.get(url, headers=headers, timeout=20)
            res.raise_for_status()
            df = pd.read_csv(io.StringIO(res.text))

            # Column name varies slightly across downloads
            sym_col = next(
                (c for c in df.columns if c.strip().upper() in ('SYMBOL', 'SYMBOLS')),
                df.columns[0]
            )
            base = df[sym_col].dropna().astype(str).tolist()
            syms = [f"{s}.NS" for s in base if s and s.lower() != 'nan' and 1 < len(s) <= 20]
            symbols.extend(list(set(syms)))
            logger.info(f"Fetched {len(syms)} NSE symbols from EQUITY_L.csv")
            fetched = True
        except Exception as e:
            logger.warning(f"NSE EQUITY_L.csv failed ({e}). Trying Fyers …")

        # — Fallback —
        if not fetched:
            try:
                url = "https://public.fyers.in/sym_details/NSE_CM.csv"
                res = requests.get(url, headers=headers, timeout=20)
                res.raise_for_status()
                df = pd.read_csv(io.StringIO(res.text), header=None, low_memory=False)
                col = _find_nse_ticker_col(df)
                if col is not None:
                    suffix_pat = re.compile(r'-(EQ|BE|SM|BL|IL|N[0-9]+)$')
                    raw = df[col].dropna().astype(str).tolist()
                    cleaned = [suffix_pat.sub('', s).strip() for s in raw]
                    syms = [f"{s}.NS" for s in cleaned if s and 1 < len(s) <= 20 and s.lower() != 'nan']
                    symbols.extend(list(set(syms)))
                    logger.info(f"Fetched {len(syms)} NSE symbols from Fyers (col={col})")
                else:
                    logger.error("Fyers NSE CSV: could not auto-detect symbol column")
            except Exception as e2:
                logger.error(f"Fyers NSE fallback also failed: {e2}")

    # -----------------------------------------------------------------------
    # All BSE  (used for both "All BSE" and "All NSE & BSE")
    # Primary  : BSE public API → numeric scrip codes → .BO
    #            yfinance requires BSE scrip codes, e.g. 500325.BO NOT RELIANCE.BO
    # Fallback : Fyers BSE_CM.csv with dynamic column detection
    # -----------------------------------------------------------------------
    if universe in ["All BSE", "All NSE & BSE"]:
        fetched = False

        # — Primary: Use NSE EQUITY_L tickers with .BO suffix —
        # yfinance resolves NSE tickers on BSE fine (e.g. RELIANCE.BO).
        # Most NSE-listed large/mid caps are cross-listed on BSE.
        try:
            logger.info("Fetching All BSE symbols via NSE EQUITY_L.csv (.BO suffix) …")
            url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            res = requests.get(url, headers=headers, timeout=20)
            res.raise_for_status()
            df_eq = pd.read_csv(io.StringIO(res.text))
            sym_col = next(
                (c for c in df_eq.columns if c.strip().upper() in ('SYMBOL', 'SYMBOLS')),
                df_eq.columns[0]
            )
            base = df_eq[sym_col].dropna().astype(str).tolist()
            syms = [f"{s}.BO" for s in base if s and s.lower() != 'nan' and 1 < len(s) <= 20]
            symbols.extend(list(set(syms)))
            logger.info(f"Fetched {len(syms)} BSE symbols (cross-listed via EQUITY_L)")
            fetched = True
        except Exception as e:
            logger.warning(f"NSE EQUITY_L for BSE failed ({e}). Trying Fyers BSE CSV …")

        # — Fallback: Fyers BSE_CM.csv — numeric scrip codes (col 12 confirmed) —
        if not fetched:
            try:
                url = "https://public.fyers.in/sym_details/BSE_CM.csv"
                res = requests.get(url, headers=headers, timeout=20)
                res.raise_for_status()
                df = pd.read_csv(io.StringIO(res.text), header=None, low_memory=False)
                col = _find_bse_scrip_col(df)
                if col is not None:
                    raw = df[col].dropna().astype(str).tolist()
                    syms = [f"{s}.BO" for s in raw if s.isdigit() and 4 <= len(s) <= 7]
                    symbols.extend(list(set(syms)))
                    logger.info(f"Fetched {len(syms)} BSE scrip codes from Fyers (col={col})")
                else:
                    logger.error("Fyers BSE CSV: could not auto-detect scrip code column")
            except Exception as e2:
                logger.error(f"Fyers BSE fallback also failed: {e2}")

    return symbols


# ---------------------------------------------------------------------------
# Data fetcher for strategy evaluation
# ---------------------------------------------------------------------------
def fetch_data_for_strategy(symbol, strategy_id):
    """
    Fetches historical OHLCV data for a symbol on the timeframe required by
    the given strategy.
    Expected symbol format: 'RELIANCE.NS'  or  '500325.BO'
    """
    from datetime import date, timedelta
    try:
        if strategy_id == "52w":
            # We need EXACTLY 52 + 1 (current) = 53 weekly bars.
            # Using period="2y" is unreliable — if yfinance drops NaN rows
            # (holidays / incomplete weeks), the tail slice covers fewer than
            # 52 actual calendar weeks.
            #
            # Fix: fetch by explicit date range.
            #   • end   = today (gets the current in-progress week)
            #   • start = 57 weeks ago  (52 required + 5-week safety buffer
            #             to absorb any NaN-dropped rows and still have >= 53)
            end_date   = date.today()
            start_date = end_date - timedelta(weeks=57)
            df = yf.download(
                tickers=symbol,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                interval="1wk",
                progress=False,
                auto_adjust=False,
            )
        elif strategy_id == "ath":
            # Need maximum data to find all-time high.
            df = yf.download(tickers=symbol, period="max", interval="1wk",
                             progress=False, auto_adjust=False)
        elif strategy_id == "5m":
            # Need at least 6 monthly bars. 2 years is safe.
            df = yf.download(tickers=symbol, period="2y", interval="1mo",
                             progress=False, auto_adjust=False)
        else:
            return None

        if df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = [col.lower() for col in df.columns]
        df.index.name = 'date'

        # Drop rows with NaN in OHLCV (can occur on incomplete weeks/months)
        df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
        return df

    except Exception as e:
        logger.error(f"Exception fetching data for {symbol}: {str(e)}")
        return None
