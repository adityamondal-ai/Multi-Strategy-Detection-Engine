import requests
import pandas as pd
import io

def test_fetch(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"URL: {url} - Status: {res.status_code}")
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            print(df.head())
    except Exception as e:
        print(f"Error: {e}")

test_fetch("https://archives.nseindia.com/content/indices/ind_nifty50list.csv")
test_fetch("https://archives.nseindia.com/content/indices/ind_nifty500list.csv")
