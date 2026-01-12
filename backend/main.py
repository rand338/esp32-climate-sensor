from flask import Flask, request, jsonify, render_template_string
import sqlite3
import datetime
import config 

app = Flask(__name__)

# --- DATABASE ---
def get_db_connection():
    conn = sqlite3.connect(config.DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS measurements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  device_id TEXT,
                  temperature REAL, 
                  humidity REAL, 
                  pressure REAL, 
                  gas_resistance REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IoT Multi-Sensor Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #1a1a1a; color: #eee; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #03a9f4; text-align: center; margin-bottom: 10px; }
        
        /* Device Selector */
        .device-selector { text-align: center; margin-bottom: 20px; }
        select { 
            background: #333; color: #eee; border: 1px solid #555; 
            padding: 8px 16px; font-size: 1rem; border-radius: 4px; 
        }

        /* Controls */
        .controls { text-align: center; margin-bottom: 20px; }
        .btn { 
            background: #333; color: #eee; border: 1px solid #555; 
            padding: 8px 16px; margin: 0 5px; cursor: pointer; border-radius: 4px; 
            transition: background 0.3s;
        }
        .btn:hover { background: #444; }
        .btn.active { background: #03a9f4; border-color: #03a9f4; color: #fff; }

        /* Stats Cards - Getrennt & Flexibel */
        .stats-row { display: flex; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }
        .card { 
            background: #333; padding: 15px; border-radius: 8px; text-align: center; 
            width: 140px; border-top: 3px solid #777; 
            /* Temp/Hum sind immer sichtbar, andere hidden by default */
        }
        .card-hidden { display: none; } 
        .val { font-size: 1.8rem; font-weight: bold; }
        .label { color: #aaa; font-size: 0.9rem; }

        /* Chart Containers */
        .chart-wrapper { margin-bottom: 30px; } 
        .chart-wrapper-hidden { display: none; }
        .chart-container { 
            background: #2a2a2a; border-radius: 12px; padding: 15px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); height: 300px;
        }
        h3.chart-title { margin: 0 0 10px 10px; font-size: 1rem; color: #bbb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Climate Dashboard</h1>
        
        <div class="device-selector">
            <label for="deviceSelect">Sensor: </label>
            <select id="deviceSelect" onchange="changeDevice()"><option value="">Loading...</option></select>
        </div>

        <!-- 1. Kacheln (Alle getrennt) -->
        <div class="stats-row">
            <!-- Immer sichtbar -->
            <div class="card" style="border-color: #ff6384">
                <div class="label">Temperature</div><div class="val" id="cur-temp">--</div>
            </div>
            <div class="card" style="border-color: #36a2eb">
                <div class="label">Humidity</div><div class="val" id="cur-hum">--</div>
            </div>
            
            <!-- Optional sichtbar -->
            <div id="card-pres" class="card card-hidden" style="border-color: #4bc0c0">
                <div class="label">Pressure</div><div class="val" id="cur-pres">--</div>
            </div>
            <div id="card-gas" class="card card-hidden" style="border-color: #ffcd56">
                <div class="label">Air Quality</div><div class="val" id="cur-gas">--</div>
            </div>
        </div>

        <div class="controls">
            <button class="btn" onclick="setRange('hour', this)">1 Hour</button>
            <button class="btn active" onclick="setRange('day', this)">24 Hours</button>
            <button class="btn" onclick="setRange('week', this)">7 Days</button>
            <button class="btn" onclick="setRange('month', this)">30 Days</button>
        </div>

        <!-- 2. Charts -->
        
        <!-- Main Chart: Temp + Hum (Combined) -->
        <div class="chart-wrapper">
            <h3 class="chart-title">Climate Overview (Temp & Humidity)</h3>
            <div class="chart-container"><canvas id="tempHumChart"></canvas></div>
        </div>

        <!-- Pressure Chart (Optional) -->
        <div id="wrap-pres" class="chart-wrapper chart-wrapper-hidden">
            <h3 class="chart-title">Atmospheric Pressure (hPa)</h3>
            <div class="chart-container"><canvas id="presChart"></canvas></div>
        </div>

        <!-- Gas Chart (Optional) -->
        <div id="wrap-gas" class="chart-wrapper chart-wrapper-hidden">
            <h3 class="chart-title">Air Quality (Gas Resistance)</h3>
            <div class="chart-container"><canvas id="gasChart"></canvas></div>
        </div>
    </div>

<script>
    const use12h = {{ 'true' if use_12h else 'false' }};
    const fmtFull = use12h ? 'MM/dd hh:mm aa' : 'dd.MM HH:mm';
    const fmtHour = use12h ? 'hh:mm aa' : 'HH:mm';
    const fmtDay  = use12h ? 'MM/dd' : 'dd.MM';

    let currentRange = 'day';
    let currentDevice = ''; 
    let charts = { main: null, pres: null, gas: null };

    // Init
    async function loadDevices() {
        try {
            const res = await fetch('/api/devices');
            const devices = await res.json();
            const select = document.getElementById('deviceSelect');
            select.innerHTML = '';
            
            if (devices.length === 0) { select.innerHTML = '<option>No devices found</option>'; return; }
            
            devices.forEach(dev => {
                const opt = document.createElement('option');
                opt.value = dev; opt.innerText = dev; select.appendChild(opt);
            });
            
            if (!currentDevice && devices.length > 0) currentDevice = devices[0];
            select.value = currentDevice;
            loadData(); 
        } catch(e) { console.error(e); }
    }

    function changeDevice() { currentDevice = document.getElementById('deviceSelect').value; loadData(); }
    
    function setRange(range, btnElement) {
        currentRange = range;
        document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
        btnElement.classList.add('active');
        loadData();
    }

    async function loadData() {
        if (!currentDevice) return;

        try {
            const response = await fetch(`/api/history?range=${currentRange}&device_id=${currentDevice}`);
            const data = await response.json();
            
            const times = data.map(d => new Date(d.timestamp.replace(" ", "T") + "Z"));
            const temps = data.map(d => d.temperature);
            const hums  = data.map(d => d.humidity);
            const press = data.map(d => d.pressure);
            const gases = data.map(d => d.gas_resistance / 1000.0);

            // Check availability (Is value > 0 anywhere in the dataset?)
            const hasPres = press.some(v => v > 0);
            const hasGas  = gases.some(v => v > 0);

            // Update Cards (Values)
            if (data.length > 0) {
                const last = data[data.length - 1];
                document.getElementById('cur-temp').innerText = last.temperature.toFixed(1) + " °C";
                document.getElementById('cur-hum').innerText  = last.humidity.toFixed(0) + " %";
                document.getElementById('cur-pres').innerText = last.pressure.toFixed(0) + " hPa";
                document.getElementById('cur-gas').innerText  = (last.gas_resistance / 1000).toFixed(1);
            }

            // --- CHART 1: Temp & Hum (Combined, Dual Axis) ---
            const ctxMain = document.getElementById('tempHumChart').getContext('2d');
            if (charts.main) charts.main.destroy();
            charts.main = new Chart(ctxMain, {
                type: 'line',
                data: {
                    labels: times,
                    datasets: [
                        {
                            label: 'Temperature (°C)',
                            data: temps,
                            borderColor: '#ff6384', backgroundColor: '#ff638433',
                            yAxisID: 'y',
                            fill: true, tension: 0.3, pointRadius: currentRange === 'hour' ? 3 : 0
                        },
                        {
                            label: 'Humidity (%)',
                            data: hums,
                            borderColor: '#36a2eb',
                            yAxisID: 'y1',
                            fill: false, tension: 0.3, pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    scales: {
                        x: { type: 'time', time: { tooltipFormat: fmtFull, displayFormats: { minute: fmtHour, hour: fmtHour, day: fmtDay } }, grid: { color: '#444' } },
                        y:  { type: 'linear', display: true, position: 'left', title: {display: true, text: '°C'}, grid: { color: '#444' } },
                        y1: { type: 'linear', display: true, position: 'right', title: {display: true, text: '%'}, grid: { drawOnChartArea: false } }
                    }
                }
            });

            // --- CHART 2: Pressure (Conditional) ---
            toggleSection('pres', hasPres);
            if(hasPres) renderSingleChart('pres', 'presChart', 'Pressure (hPa)', '#4bc0c0', times, press);

            // --- CHART 3: Gas (Conditional) ---
            toggleSection('gas', hasGas);
            if(hasGas) renderSingleChart('gas', 'gasChart', 'Gas Resistance (kOhm)', '#ffcd56', times, gases);

        } catch (err) { console.error(err); }
    }

    // Helper for single charts
    function renderSingleChart(key, ctxId, label, color, times, dataPoints) {
        const ctx = document.getElementById(ctxId).getContext('2d');
        if (charts[key]) charts[key].destroy();
        charts[key] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: times,
                datasets: [{
                    label: label, data: dataPoints, borderColor: color, backgroundColor: color + '33',
                    borderWidth: 2, tension: 0.3, fill: true, pointRadius: currentRange === 'hour' ? 3 : 0
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: { type: 'time', time: { tooltipFormat: fmtFull, displayFormats: { minute: fmtHour, hour: fmtHour, day: fmtDay } }, grid: { color: '#444' } },
                    y: { grid: { color: '#444' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // Toggle visibility of Card AND Chart
    function toggleSection(key, isVisible) {
        const displayStyle = isVisible ? 'block' : 'none';
        
        // Toggle Card
        const card = document.getElementById('card-' + key);
        if(card) {
             if(isVisible) card.classList.remove('card-hidden');
             else card.classList.add('card-hidden');
        }

        // Toggle Chart Wrapper
        const wrapper = document.getElementById('wrap-' + key);
        if(wrapper) {
             if(isVisible) wrapper.classList.remove('chart-wrapper-hidden');
             else wrapper.classList.add('chart-wrapper-hidden');
        }
    }

    loadDevices();
    setInterval(loadData, 30000); 
</script>
</body>
</html>
"""


# --- ROUTES (No Changes Needed) ---
@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, use_12h=config.TIME_FORMAT_12H)

@app.route('/api/devices')
def get_devices():
    conn = get_db_connection()
    devices = conn.execute("SELECT DISTINCT device_id FROM measurements WHERE device_id IS NOT NULL").fetchall()
    conn.close()
    device_list = [d['device_id'] for d in devices]
    return jsonify(device_list)

@app.route('/api/history')
def get_history():
    time_range = request.args.get('range', 'day')
    device_id = request.args.get('device_id')
    
    conn = get_db_connection()
    where_clause = "WHERE 1=1"
    params = []
    
    if device_id:
        where_clause += " AND device_id = ?"
        params.append(device_id)
        
    time_filter = ""
    if time_range == 'hour': time_filter = "AND timestamp >= datetime('now', '-1 hour')"
    elif time_range == 'day': time_filter = "AND timestamp >= datetime('now', '-24 hours')"
    elif time_range == 'week': time_filter = "AND timestamp >= datetime('now', '-7 days')"
    elif time_range == 'month': time_filter = "AND timestamp >= datetime('now', '-1 month')"
    
    where_clause += f" {time_filter}"

    query = ""
    if time_range in ['week', 'month']:
        query = f"""
            SELECT strftime('%Y-%m-%d %H:00:00', timestamp) as ts_group, 
                   AVG(temperature) as temperature, 
                   AVG(humidity) as humidity, 
                   AVG(pressure) as pressure, 
                   AVG(gas_resistance) as gas_resistance
            FROM measurements 
            {where_clause}
            GROUP BY ts_group 
            ORDER BY ts_group ASC
        """
    else:
        query = f"""
            SELECT timestamp, temperature, humidity, pressure, gas_resistance 
            FROM measurements 
            {where_clause}
            ORDER BY timestamp ASC
        """

    try:
        cursor = conn.execute(query, params)
        measurements = cursor.fetchall()
        conn.close()
        
        data = []
        for m in measurements:
            keys = m.keys()
            ts = m['timestamp'] if 'timestamp' in keys else m['ts_group']
            data.append({
                "timestamp": ts, 
                "temperature": m['temperature'],
                "humidity": m['humidity'],
                "pressure": m['pressure'],
                "gas_resistance": m['gas_resistance']
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/post-data', methods=['POST'])
def post_data():
    received_key = request.form.get('api_key')
    if received_key != config.API_KEY:
        return jsonify({"status": "error", "message": "Invalid API Key"}), 403

    try:
        device_id = request.form.get('device_id', 'unknown')
        temp = float(request.form.get('temperature'))
        hum = float(request.form.get('humidity'))
        pres = float(request.form.get('pressure'))
        gas = float(request.form.get('gas'))
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO measurements (timestamp, device_id, temperature, humidity, pressure, gas_resistance) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)",
                  (device_id, temp, hum, pres, gas))
        conn.commit()
        conn.close()
        print(f"[{datetime.datetime.now()}] Saved from {device_id}: {temp}°C")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
