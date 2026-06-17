document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const modal = document.getElementById("settingsModal");
    const btnSettings = document.getElementById("btnSettings");
    const spanClose = document.getElementsByClassName("close")[0];
    const settingsForm = document.getElementById("settingsForm");
    const btnScan = document.getElementById("btnScan");
    const btnStopScan = document.getElementById("btnStopScan");
    const tbody = document.querySelector("#entriesTable tbody");
    const activeAlertsCount = document.getElementById("activeAlertsCount");
    const strategySelect = document.getElementById("strategySelect");
    
    // Tab Elements
    const tabRecent = document.getElementById("tabRecent");
    const tabWatchlist = document.getElementById("tabWatchlist");
    const btnClearHistory = document.getElementById("btnClearHistory");
    let currentTab = "recent"; // "recent" or "watchlist"

    // Modal logic
    btnSettings.onclick = () => {
        loadSettings();
        modal.style.display = "flex";
    }

    spanClose.onclick = () => {
        modal.style.display = "none";
    }

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    // Load Settings
    function loadSettings() {
        fetch('/api/settings')
            .then(res => res.json())
            .then(response => {
                if(response.status === 'success') {
                    const data = response.data;
                    document.getElementById('SMTP_EMAIL').value = data.SMTP_EMAIL || '';
                    document.getElementById('SMTP_PASSWORD').value = data.SMTP_PASSWORD || '';
                    document.getElementById('ALERT_EMAIL').value = data.ALERT_EMAIL || '';
                    document.getElementById('MAX_STOCK_PRICE').value = data.MAX_STOCK_PRICE || '';
                    if (data.UNIVERSE) {
                        document.getElementById('UNIVERSE').value = data.UNIVERSE;
                        const universeDropdown = document.getElementById('universeDropdown');
                        if (universeDropdown) {
                            universeDropdown.querySelector('.custom-dropdown-selected').textContent = data.UNIVERSE;
                            universeDropdown.querySelectorAll('.custom-dropdown-option').forEach(opt => {
                                opt.classList.toggle('selected', opt.getAttribute('data-value') === data.UNIVERSE);
                            });
                        }
                    }
                    document.getElementById('ENABLE_VOLUME_FILTER').checked = (data.ENABLE_VOLUME_FILTER === 'true');
                    document.getElementById('MIN_VOLUME').value = data.MIN_VOLUME || '';
                    document.getElementById('ENABLE_WEEKLY_VOLUME_FILTER').checked = (data.ENABLE_WEEKLY_VOLUME_FILTER === 'true');
                    document.getElementById('MIN_WEEKLY_VOLUME').value = data.MIN_WEEKLY_VOLUME || '';
                }
            })
            .catch(err => console.error("Error loading settings:", err));
    }

    // Save Settings
    settingsForm.onsubmit = (e) => {
        e.preventDefault();
        const payload = {
            SMTP_EMAIL: document.getElementById('SMTP_EMAIL').value,
            SMTP_PASSWORD: document.getElementById('SMTP_PASSWORD').value,
            ALERT_EMAIL: document.getElementById('ALERT_EMAIL').value,
            MAX_STOCK_PRICE: document.getElementById('MAX_STOCK_PRICE').value,
            UNIVERSE: document.getElementById('UNIVERSE').value,
            ENABLE_VOLUME_FILTER: document.getElementById('ENABLE_VOLUME_FILTER').checked ? 'true' : 'false',
            MIN_VOLUME: document.getElementById('MIN_VOLUME').value,
            ENABLE_WEEKLY_VOLUME_FILTER: document.getElementById('ENABLE_WEEKLY_VOLUME_FILTER').checked ? 'true' : 'false',
            MIN_WEEKLY_VOLUME: document.getElementById('MIN_WEEKLY_VOLUME').value
        };

        fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                alert('Settings saved successfully!');
                modal.style.display = "none";
            }
        })
        .catch(err => console.error("Error saving settings:", err));
    };

    // Strategy Change
    strategySelect.onchange = () => {
        loadEntries();
    };

    // Trigger Scan
    btnScan.onclick = () => {
        btnScan.disabled = true;
        btnScan.innerText = "Scanning...";
        if (btnStopScan) btnStopScan.style.display = "inline-block";
        
        const payload = { strategy_id: strategySelect.value };
        
        fetch('/api/scan', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                btnScan.disabled = false;
                btnScan.innerText = "Manual Scan";
                if (btnStopScan) btnStopScan.style.display = "none";
            })
            .catch(err => {
                console.error("Error triggering scan:", err);
                btnScan.disabled = false;
                btnScan.innerText = "Manual Scan";
                if (btnStopScan) btnStopScan.style.display = "none";
            });
    };

    if (btnStopScan) {
        btnStopScan.onclick = () => {
            fetch('/api/stop_scan', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                })
                .catch(err => console.error("Error stopping scan:", err));
        };
    }

    // Tab logic
    tabRecent.onclick = () => {
        currentTab = "recent";
        tabRecent.classList.add("active");
        tabWatchlist.classList.remove("active");
        if(btnClearHistory) btnClearHistory.style.display = "block";
        loadEntries();
    };

    tabWatchlist.onclick = () => {
        currentTab = "watchlist";
        tabWatchlist.classList.add("active");
        tabRecent.classList.remove("active");
        if(btnClearHistory) btnClearHistory.style.display = "none";
        loadEntries();
    };

    if (btnClearHistory) {
        btnClearHistory.onclick = () => {
            if (confirm("Are you sure you want to clear history for this strategy?")) {
                const payload = { strategy_id: strategySelect.value };
                fetch('/api/clear_history', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === 'success') {
                            loadEntries();
                        }
                    })
                    .catch(err => console.error("Error clearing history:", err));
            }
        };
        // Set initial display
        btnClearHistory.style.display = currentTab === "recent" ? "block" : "none";
    }

    window.toggleWatchlist = (symbol, date, price, sl, tp, isRemoving, id, riskStatus, capitalUsage) => {
        const url = isRemoving ? '/api/watchlist/remove' : '/api/watchlist/add';
        const payload = isRemoving 
            ? { id } 
            : { symbol, entry_date: date, entry_price: price, sl, tp, risk_status: riskStatus, capital_usage: capitalUsage, strategy_id: strategySelect.value };
        
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                loadEntries();
            }
        });
    };

    // Load Status
    function loadStatus() {
        fetch('/api/status')
            .then(res => res.json())
            .then(response => {
                if(response.status === 'success') {
                    document.getElementById('lastScanTime').textContent = response.last_scan_time;

                    // Sync button states
                    if (response.is_scanning) {
                        btnScan.disabled = true;
                        btnScan.innerText = "Scanning...";
                        if (btnStopScan) btnStopScan.style.display = "inline-block";
                    } else {
                        btnScan.disabled = false;
                        btnScan.innerText = "Manual Scan";
                        if (btnStopScan) btnStopScan.style.display = "none";
                    }
                }
            })
            .catch(err => console.error("Error loading status:", err));
    }

    let lastEntriesJSON = {};
    let currentlyDisplayedStratTab = "";

    // Load Entries
    function loadEntries() {
        const strat = strategySelect.value;
        const currentStratTab = strat + currentTab;
        const url = currentTab === "recent" ? `/api/entries?strategy_id=${strat}` : `/api/watchlist?strategy_id=${strat}`;
        
        fetch(url)
            .then(res => res.json())
            .then(response => {
                if(response.status === 'success') {
                    const entries = response.data;
                    if(currentTab === "recent") {
                        activeAlertsCount.innerText = entries.length;
                    }

                    const currentJSON = JSON.stringify(entries);
                    if (currentlyDisplayedStratTab === currentStratTab && lastEntriesJSON[currentStratTab] === currentJSON) {
                        return; // No changes, skip DOM update to prevent repeating animations
                    }
                    lastEntriesJSON[currentStratTab] = currentJSON;
                    currentlyDisplayedStratTab = currentStratTab;
                    
                    tbody.innerHTML = '';
                    let lastDate = null;
                    let serialNo = 1;
                    
                    entries.forEach(entry => {
                        if (entry.entry_date !== lastDate) {
                            lastDate = entry.entry_date;
                            serialNo = 1; 
                            
                            const divider = document.createElement('tr');
                            divider.innerHTML = `<td colspan="10" style="background: rgba(255,255,255,0.05); text-align: center; font-weight: bold; padding: 10px; color: var(--accent-color);">Scan Session: ${entry.entry_date}</td>`;
                            tbody.appendChild(divider);
                        }
                        
                        const riskPct = (((entry.entry_price - entry.sl) / entry.entry_price) * 100).toFixed(2);
                        const rewardPct = (((entry.tp - entry.entry_price) / entry.entry_price) * 100).toFixed(2);
                        const actionBtn = currentTab === "recent" 
                            ? `<button class="action-btn" title="Add to Watchlist" onclick="toggleWatchlist('${entry.symbol}', '${entry.entry_date}', ${entry.entry_price}, ${entry.sl}, ${entry.tp}, false, null, '${entry.risk_status}', '${entry.capital_usage}')">⭐</button>`
                            : `<button class="action-btn" title="Remove from Watchlist" onclick="toggleWatchlist(null, null, null, null, null, true, ${entry.id})">❌</button>`;
                            
                        const isHighRisk = parseFloat(riskPct) > 25.9;
                        const riskStatusStyle = isHighRisk 
                            ? 'background: rgba(239, 68, 68, 0.2); color: var(--danger-color); padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;'
                            : 'background: rgba(16, 185, 129, 0.2); color: var(--success-color); padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;';
                            
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${serialNo++}</td>
                            <td><strong style="color: var(--accent-color);">${entry.symbol}</strong></td>
                            <td>${entry.entry_date}</td>
                            <td>₹${entry.entry_price.toFixed(2)}</td>
                            <td style="color: var(--danger-color);">₹${entry.sl.toFixed(2)} (${riskPct}% Risk)</td>
                            <td style="color: var(--success-color);">₹${entry.tp.toFixed(2)} (${rewardPct}% Reward)</td>
                            <td><span style="${riskStatusStyle}">${entry.risk_status || 'N/A'}</span></td>
                            <td>${entry.capital_usage || 'N/A'}</td>
                            <td><span style="background: rgba(16, 185, 129, 0.2); color: var(--success-color); padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">${entry.status || 'Saved'}</span></td>
                            <td>${actionBtn}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            })
            .catch(err => console.error("Error loading entries:", err));
    }
    // Custom Dropdown Logic
    function setupCustomDropdowns() {
        document.querySelectorAll('.custom-dropdown').forEach(dropdown => {
            const selectedDisplay = dropdown.querySelector('.custom-dropdown-selected');
            const options = dropdown.querySelectorAll('.custom-dropdown-option');
            const hiddenInput = dropdown.querySelector('input[type="hidden"]');

            selectedDisplay.onclick = (e) => {
                e.stopPropagation();
                // Close other dropdowns
                document.querySelectorAll('.custom-dropdown').forEach(d => {
                    if (d !== dropdown) d.classList.remove('open');
                });
                dropdown.classList.toggle('open');
            };

            options.forEach(option => {
                option.onclick = (e) => {
                    e.stopPropagation();
                    const value = option.getAttribute('data-value');
                    const text = option.textContent;
                    
                    // Update display
                    selectedDisplay.textContent = text;
                    
                    // Update selection state
                    options.forEach(opt => opt.classList.remove('selected'));
                    option.classList.add('selected');
                    
                    // Update hidden input and trigger change if needed
                    hiddenInput.value = value;
                    if(hiddenInput.id === 'strategySelect') {
                        loadEntries();
                    }
                    
                    dropdown.classList.remove('open');
                };
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', () => {
            document.querySelectorAll('.custom-dropdown').forEach(dropdown => {
                dropdown.classList.remove('open');
            });
        });
    }

    setupCustomDropdowns();

    // Initial load
    loadStatus();
    loadEntries();
    // Refresh entries and status every 3 seconds
    setInterval(() => {
        loadStatus();
        loadEntries();
    }, 3000);
});
