from flask import Flask, render_template, request, jsonify
import logging
import threading
import sys
import os

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from database import init_db, get_all_entries, get_setting, set_setting, get_all_watchlist, add_to_watchlist, remove_from_watchlist, clear_entries
import strategy

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

base_dir = get_base_path()
app = Flask(__name__, 
            static_folder=os.path.join(base_dir, 'static'), 
            template_folder=os.path.join(base_dir, 'templates'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/entries', methods=['GET'])
def api_get_entries():
    strategy_id = request.args.get('strategy_id', '52w')
    entries = get_all_entries(strategy_id)
    return jsonify({"status": "success", "data": entries})

@app.route('/api/clear_history', methods=['POST'])
def api_clear_history():
    data = request.json
    strategy_id = data.get('strategy_id', '52w')
    clear_entries(strategy_id)
    return jsonify({"status": "success"})

@app.route('/api/watchlist', methods=['GET'])
def api_get_watchlist():
    strategy_id = request.args.get('strategy_id', '52w')
    entries = get_all_watchlist(strategy_id)
    return jsonify({"status": "success", "data": entries})

@app.route('/api/watchlist/add', methods=['POST'])
def api_add_watchlist():
    data = request.json
    risk_status = data.get('risk_status', 'N/A')
    capital_usage = data.get('capital_usage', 'N/A')
    strategy_id = data.get('strategy_id', '52w')
    add_to_watchlist(data['symbol'], data['entry_date'], data['entry_price'], data['sl'], data['tp'], risk_status, capital_usage, strategy_id)
    return jsonify({"status": "success"})

@app.route('/api/watchlist/remove', methods=['POST'])
def api_remove_watchlist():
    data = request.json
    remove_from_watchlist(data['id'])
    return jsonify({"status": "success"})

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "data": {
                "SMTP_EMAIL": get_setting("SMTP_EMAIL", ""),
                "SMTP_PASSWORD": "********" if get_setting("SMTP_PASSWORD") else "",
                "ALERT_EMAIL": get_setting("ALERT_EMAIL", ""),
                "MAX_STOCK_PRICE": get_setting("MAX_STOCK_PRICE", "5000"),
                "UNIVERSE": get_setting("UNIVERSE", "Nifty 500"),
                "ENABLE_VOLUME_FILTER": get_setting("ENABLE_VOLUME_FILTER", "false"),
                "MIN_VOLUME": get_setting("MIN_VOLUME", ""),
                "ENABLE_WEEKLY_VOLUME_FILTER": get_setting("ENABLE_WEEKLY_VOLUME_FILTER", "false"),
                "MIN_WEEKLY_VOLUME": get_setting("MIN_WEEKLY_VOLUME", "")
            }
        })
    else:
        data = request.json
        keys_to_update = ["SMTP_EMAIL", "SMTP_PASSWORD", "ALERT_EMAIL", "UNIVERSE",
                          "MAX_STOCK_PRICE", "ENABLE_VOLUME_FILTER", "MIN_VOLUME",
                          "ENABLE_WEEKLY_VOLUME_FILTER", "MIN_WEEKLY_VOLUME"]
        for key in keys_to_update:
            if key in data and data[key] is not None and data[key] != "********":
                set_setting(key, data[key])
        return jsonify({"status": "success", "message": "Settings updated"})

@app.route('/api/scan', methods=['POST'])
def api_trigger_scan():
    data = request.json
    strategy_id = data.get('strategy_id', '52w')
    if strategy.is_scanning:
        return jsonify({"status": "error", "message": "Scan already in progress."})
    
    threading.Thread(target=strategy.run_scanner, args=(strategy_id,), daemon=True).start()
    return jsonify({"status": "success", "message": "Manual scan triggered. Check console for logs."})

@app.route('/api/stop_scan', methods=['POST'])
def api_stop_scan():
    strategy.stop_scan_flag = True
    return jsonify({"status": "success", "message": "Stop signal sent to scanner."})

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        "status": "success",
        "last_scan_time": get_setting("LAST_SCAN_TIME", "Never"),
        "is_scanning": strategy.is_scanning
    })

if __name__ == '__main__':
    import webview
    
    init_db()
    
    def run_server():
        app.run(host='127.0.0.1', port=5000, use_reloader=False)
        
    threading.Thread(target=run_server, daemon=True).start()
    
    window = webview.create_window('MultiScanner', 'http://127.0.0.1:5000/', width=1200, height=800, min_size=(800, 600))
    
    def on_closing():
        os._exit(0)
        
    window.events.closed += on_closing
    
    webview.start()
