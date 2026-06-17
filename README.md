# MultiScanner: Multi-Strategy Detection Engine 🚀

![MultiScanner Dashboard](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![Flask](https://img.shields.io/badge/Flask-Web_Framework-lightgrey) ![yfinance](https://img.shields.io/badge/yfinance-Market_Data-yellow)

MultiScanner is a high-performance, fully localized stock scanning engine designed for the Indian Stock Market. It leverages advanced technical analysis to scan market universes (Nifty 50, Nifty 500, All NSE, All BSE) and identify powerful trading setups based on multiple timeframes.

Wrapped in a beautifully designed, state-of-the-art glassmorphism UI, MultiScanner operates entirely locally and provides a compiled standalone `.exe` for instant execution.

---

## 🔥 Key Features

### 📈 Advanced Scanning Strategies
*   **52-Week High Breakout:** Detects stocks breaking out of a 1-year consolidation.
*   **All-Time High Breakout:** Identifies incredibly bullish stocks venturing into uncharted territory.
*   **5-Month Upper Closing:** A powerful medium-term momentum strategy that isolates stocks closing at their highest point in the last 5 months.

### ⚙️ Granular Configuration & Filtering
*   **Decoupled Volume Filters:** Run independent minimum average volume filters. Apply monthly volume criteria (e.g. 10-month avg) strictly for the 5-Month strategy without affecting the Weekly volume criteria used for the 52W/ATH strategies.
*   **Max Stock Price Filter:** Ignore penny stocks or overly expensive blue-chips by setting a strict maximum execution price.
*   **Live NSE Market Universes:** Fetches the actual live F&O constituents of **Nifty 50** and **Nifty 500** directly from the NSE Archives, or scan everything using **Fyers** symbol masters.

### 🎨 Premium Dynamic UI
*   **Glassmorphism Aesthetic:** A breathtaking deep-space animated mesh background with sleek frosted-glass containers.
*   **Custom Micro-animations:** Fully customized interactive dropdowns, cascading table row animations, and responsive hover glows.
*   **Real-time Dashboard:** Watch scan progress, track active alerts, and seamlessly manage your saved Watchlist versus Recent Scans.

### 🔔 Automated Alerting (Optional)
*   **Built-in SMTP Engine:** Connect your Gmail/SMTP server to push instant email alerts the second a breakout is detected.
*   **Completely Optional:** Don't want emails? Leave the fields blank and save your settings without any validation blocks.

---

## 🛠️ Tech Stack

*   **Backend Engine:** Python, Flask, Pandas
*   **Market Data:** `yfinance` (strictly unadjusted, raw charting data identical to TradingView), `requests`
*   **Frontend:** Vanilla JavaScript, HTML5, CSS3 (No heavy JS frameworks, purely optimized DOM manipulation)
*   **Database:** Local SQLite (`scanner.db`)
*   **Packaging:** PyInstaller (Compiled into a single executable `MultiScanner.exe`)

---

## 🚀 Getting Started

### 🏃‍♂️ Running the App (No Coding Required)
1. Go to the **Releases** section on the right side of this GitHub page.
2. Download the `MultiScanner.zip` file.
3. Right-click the downloaded file and select **Extract All...**
4. Open the extracted folder and double-click `MultiScanner.exe`.
5. A local server will instantly boot up, and the GUI will automatically open in a native window!

### 💻 Running from Source (For Developers)
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install flask pandas yfinance requests pywebview
   ```
4. Run the application:
   ```bash
   python app.py
   ```

---

## 📸 Screenshots

*(Add your screenshots here by dragging and dropping them into the README!)*

1. **The Dynamic Dashboard:** Showcasing the glassmorphism table and the custom dropdown selectors.
2. **Settings Modal:** Displaying the decoupled Weekly vs. Monthly volume filters.

---

## 📝 License

This project is intended for personal and educational use. Always do your own research before executing real trades based on scanner alerts.
