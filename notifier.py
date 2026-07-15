import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import get_setting
import logging

logger = logging.getLogger(__name__)


def _parse_symbol(sym):
    """
    Parse a yfinance symbol into (exchange, clean_ticker).

    yfinance format examples:
        RELIANCE.NS  →  ('NSE', 'RELIANCE')
        500325.BO    →  ('BSE', '500325')
        RELIANCE     →  ('NSE', 'RELIANCE')   # fallback for bare tickers
    """
    if sym.endswith('.NS'):
        return 'NSE', sym[:-3]
    elif sym.endswith('.BO'):
        return 'BSE', sym[:-3]
    else:
        # Bare symbol — assume NSE (Nifty 50/500 path)
        return 'NSE', sym


def send_bulk_email_alert(triggered_stocks, strategy_id):
    if not triggered_stocks:
        return

    sender_email = get_setting('SMTP_EMAIL')
    sender_password = get_setting('SMTP_PASSWORD')
    receiver_email = get_setting('ALERT_EMAIL')

    if not all([sender_email, sender_password, receiver_email]):
        logger.warning("SMTP credentials not configured. Skipping bulk email alert.")
        return

    strategy_names = {
        '52w': "52-Week High Breakout",
        'ath': "All-Time High Breakout",
        '5m': "5-Month Upper Closing"
    }
    strat_name = strategy_names.get(strategy_id, "Strategy Scanner")

    subject = f"BULLISH ALERT: {len(triggered_stocks)} Stocks - {strat_name}"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email

        # ── Plain-text body ──────────────────────────────────────────────
        text_lines = [
            f"The MultiScanner has detected a pattern for {len(triggered_stocks)} "
            f"stocks using the {strat_name} strategy!\n"
        ]
        for stock in triggered_stocks:
            exch, ticker = _parse_symbol(stock['symbol'])
            text_lines.append(
                f"Exchange: {exch} | Ticker: {ticker} | "
                f"CMP: ₹{stock['entry_price']:.2f} | "
                f"SL: ₹{stock['sl']:.2f} | TP: ₹{stock['tp']:.2f} | "
                f"SL%: {stock['risk_pct']:.2f}% | TP%: {stock['reward_pct']:.2f}% | "
                f"Risk: {stock['risk_status']} | Capital: {stock['capital_usage']}"
            )
        text = "\n".join(text_lines)

        # ── HTML table rows ──────────────────────────────────────────────
        table_rows = ""
        for stock in triggered_stocks:
            exch, ticker = _parse_symbol(stock['symbol'])

            if stock['risk_pct'] > 25.9:
                bg_color  = "#ea4335"
                text_color = "white"
                risk_bg   = "#fce8e6"
                risk_text  = "#d93025"
            else:
                bg_color  = "#34a853"
                text_color = "white"
                risk_bg   = "#e6f4ea"
                risk_text  = "#137333"

            table_rows += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; background-color: {bg_color}; color: {text_color};">{exch}</td>
                <td style="padding: 10px; border: 1px solid #ddd; background-color: {bg_color}; color: {text_color};"><strong>{ticker}</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; background-color: {bg_color}; color: {text_color};">{stock['entry_price']:.2f}</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d32f2f;">{stock['sl']:.2f}</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #388e3c;">{stock['tp']:.2f}</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d32f2f;">{stock['risk_pct']:.2f}%</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #388e3c;">{stock['reward_pct']:.2f}%</td>
                <td style="padding: 10px; border: 1px solid #ddd; background-color: {risk_bg}; color: {risk_text}; font-weight: bold;">{stock['risk_status']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{stock['capital_usage']}</td>
            </tr>
            """

        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 900px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #2e6c80;">{strat_name} Alert</h2>
                <p>Pattern detected for <strong>{len(triggered_stocks)}</strong> stocks using the {strat_name} strategy.</p>
                <table style="width: 100%; border-collapse: collapse; text-align: center;">
                    <tr style="background-color: #f8f8f8;">
                        <th style="padding: 10px; border: 1px solid #ddd;">Exchange</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Stock Ticker</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">CMP (₹)</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Stop Loss (₹)</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Take Profit (₹)</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">SL %</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">TP %</th>
                        <th style="padding: 10px; border: 1px solid #ddd; color: #f28b82;">Risk Status</th>
                        <th style="padding: 10px; border: 1px solid #ddd; color: #f28b82;">Capital Usage</th>
                    </tr>
                    {table_rows}
                </table>
                <p style="font-size: 0.9em; color: #666; margin-top: 20px;">Risk to Reward = 1:3</p>
            </div>
          </body>
        </html>
        """

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        msg.attach(part1)
        msg.attach(part2)

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        logger.info(f"Bulk email alert sent successfully for {len(triggered_stocks)} stocks")
        return True

    except Exception as e:
        logger.error(f"Failed to send bulk email alert: {str(e)}")
        return False
