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
   pip install flask pandas yfinance requests PyQt5 PyQtWebEngine
   ```
4. Run the application:
   ```bash
   python app.py
   ```
---

## 🔔 Setting Up Email Alerts (Gmail SMTP)

MultiScanner can send you a beautiful HTML email the moment a breakout is detected. This is **completely optional** — the scanner works fine without it.

> **The app uses Gmail's SMTP server with SSL on port 465. You must use a Gmail App Password, NOT your regular Gmail password.**

---

### Step 1 — Enable 2-Step Verification on your Google Account

Gmail App Passwords only work if 2-Step Verification is turned on.

1. Go to **[myaccount.google.com](https://myaccount.google.com)**
2. Click **Security** in the left sidebar
3. Under *"How you sign in to Google"*, click **2-Step Verification**
4. Follow the prompts to enable it

---

### Step 2 — Generate a Gmail App Password

1. Go to **[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**
   *(You must be signed in and have 2-Step Verification enabled)*
2. In the **"App name"** field, type: `MultiScanner`
3. Click **Create**
4. Google will show you a **16-character password** (e.g. `abcd efgh ijkl mnop`)
5. **Copy it immediately** — it will not be shown again
6. Remove the spaces when pasting it into the app: `abcdefghijklmnop`

---

### Step 3 — Enter Credentials in MultiScanner

1. Open MultiScanner and click the **Settings** button (top-right)
2. Fill in the following fields:

   | Field | What to enter |
   |-------|--------------|
   | **SMTP Email** | Your Gmail address (e.g. `yourname@gmail.com`) |
   | **SMTP Password / App Password** | The 16-character App Password from Step 2 (no spaces) |
   | **Alert Receiving Email** | The email where you want to receive alerts (can be the same Gmail or any other email) |

3. Click **Save Settings**

---

### Step 4 — Test It

Run a **Manual Scan**. If any stocks trigger, an email will be sent automatically. Check your inbox (and spam folder for the first email).

> **Note:** If no stocks trigger during the scan, no email is sent — this is by design.

---

### 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| *"Failed to send bulk email alert"* in logs | Double-check the App Password has no spaces and 2FA is enabled |
| Email lands in spam | Open it and click "Not spam" — subsequent emails will go to inbox |
| *"Username and Password not accepted"* | You may have entered your regular Gmail password instead of the App Password |
| App Password page not showing | Make sure 2-Step Verification is fully enabled first |
| Want to use a different email provider | Change `smtp.gmail.com` and port `465` in `notifier.py` to match your provider's SMTP settings |

---

### 📧 Using Other Email Providers

The app is hardcoded for Gmail SSL (`smtp.gmail.com:465`). To use another provider, edit `notifier.py` line 121:

```python
# Gmail (default)
server = smtplib.SMTP_SSL('smtp.gmail.com', 465)

# Outlook / Hotmail
server = smtplib.SMTP('smtp.office365.com', 587)
server.starttls()

# Yahoo Mail
server = smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465)
```

---

## 📝 License

This project is intended for personal and educational use. Always do your own research before executing real trades based on scanner alerts.
