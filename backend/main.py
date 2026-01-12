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
    # Updated Schema with device_id
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

        .controls { text-align: center; margin-bottom: 20px; }
        .btn { 
            background: #333; color: #eee; border: 1px solid #555; 
            padding: 8px 16px; margin: 0 5px; cursor: pointer; border-radius: 4px; 
            transition: background 0.3s;
        }
        .btn:hover { background: #444; }
        .btn.active { background: #03a9f4; border-color: #03a9f4; color: #fff; }

        .chart-container { 
            background: #2a2a2a; border-radius: 12px; padding: 15px; 
            margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); height: 300px;
        }
        .stats-row { display: flex; justify-content: space-around; margin-bottom: 20px; flex-wrap: wrap; }
        .card { background: #333; padding: 15px; border-radius: 8px; text-align: center; width: 140px; margin: 5px; border-top: 3px solid #777; }
        .val { font-size: 1.8rem; font-weight: bold; }
        .label { color: #aaa; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Climate Dashboard</h1>
        
        <!-- Device Selector -->
        <div class="device-selector">
            <label for="deviceSelect">Sensor: </label>
            <select id="deviceSelect" onchange="changeDevice()">
                <option value="">Loading...</option>
            </select>
        </div>

        <div class="stats-row">
            <div class="card" style="border-color: #ff6384"><div class="label">Temperature</div><div class="val" id="cur-temp">--</div></div>
            <div class="card" style="border-color: #36a2eb"><div class="label">Humidity</div><div class="val" id="cur-hum">--</div></div>
            <div class="card" style="border-color: #4bc0c0"><div class="label">Pressure</div><div class="val" id="cur-pres">--</div></div>
            <div class="card" style="border-color: #ffcd56"><div class="label">Gas (kOhm)</div><div class="val" id="cur-gas">--</div></div>
        </div>

        <div class="controls">
            <button class="btn" onclick="setRange('hour', this)">1 Hour</button>
            <button class="btn active" onclick="setRange('day', this)">24 Hours</button>
            <button class="btn" onclick="setRange('week', this)">7 Days</button>
            <button class="btn" onclick="setRange('month', this)">30 Days</button>
        </div>

        <div class="chart-container"><canvas id="tempChart"></canvas></div>
        <div class="chart-container"><canvas id="humChart"></canvas></div>
    </div>

<script>
    const use12h = {{ 'true' if use_12h else 'false' }};
    const fmtFull   = use12h ? 'MM/dd hh:mm aa' : 'dd.MM HH:mm';
    const fmtHour   = use12h ? 'hh:mm aa'       : 'HH:mm';
    const fmtMinute = use12h ? 'hh:mm aa'       : 'HH:mm';
    const fmtDay    = use12h ? 'MM/dd'          : 'dd.MM';

    let currentRange = 'day';
    let currentDevice = ''; // Stores selected MAC address

    const commonOptions = {
        responsive: true, maintainAspectRatio: false,
        scales: {
            x: {
                type: 'time',
                time: { 
                    tooltipFormat: fmtFull,
                    displayFormats: { minute: fmtMinute, hour: fmtHour, day: fmtDay } 
                },
                grid: { color: '#444' }, ticks: { color: '#aaa' }
            },
            y: { grid: { color: '#444' }, ticks: { color: '#aaa' } }
        },
        plugins: { legend: { labels: { color: '#eee' } } }
    };

    let tempChart, humChart;

    // 1. Load Device List
    async function loadDevices() {
        try {
            const res = await fetch('/api/devices');
            const devices = await res.json();
            const select = document.getElementById('deviceSelect');
            select.innerHTML = '';
            
            if (devices.length === 0) {
                select.innerHTML = '<option>No devices found</option>';
                return;
            }

            devices.forEach(dev => {
                const opt = document.createElement('option');
                opt.value = dev;
                opt.innerText = dev; // Shows MAC Address
                select.appendChild(opt);
            });
            
            // Select first device by default
            if (!currentDevice && devices.length > 0) {
                currentDevice = devices[0];
            }
            select.value = currentDevice;
            loadData(); // Load data for this device
        } catch(e) { console.error(e); }
    }

    function changeDevice() {
        const select = document.getElementById('deviceSelect');
        currentDevice = select.value;
        loadData();
    }

    function setRange(range, btnElement) {
        currentRange = range;
        document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
        btnElement.classList.add('active');
        loadData();
    }

    async function loadData() {
        if (!currentDevice) return;

        try {
            // Fetch data filtered by device and range
            const response = await fetch(`/api/history?range=${currentRange}&device_id=${currentDevice}`);
            const data = await response.json();
            
            const times = data.map(d => new Date(d.timestamp.replace(" ", "T") + "Z"));
            const temps = data.map(d => d.temperature);
            const hums = data.map(d => d.humidity);
            const gases = data.map(d => d.gas_resistance / 1000.0); 

            if (data.length > 0) {
                const last = data[data.length - 1];
                document.getElementById('cur-temp').innerText = last.temperature.toFixed(1) + " °C";
                document.getElementById('cur-hum').innerText = last.humidity.toFixed(0) + " %";
                document.getElementById('cur-pres').innerText = last.pressure.toFixed(0) + " hPa";
                document.getElementById('cur-gas').innerText = (last.gas_resistance / 1000).toFixed(1);
            } else {
                // Reset if no data for range
                document.getElementById('cur-temp').innerText = "--";
            }

            const ctxTemp = document.getElementById('tempChart').getContext('2d');
            if (tempChart) tempChart.destroy();
            tempChart = new Chart(ctxTemp, {
                type: 'line',
                data: {
                    labels: times,
                    datasets: [{
                        label: 'Temperature (°C)', data: temps,
                        borderColor: '#ff6384', backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderWidth: 2, tension: 0.3, fill: true,
                        pointRadius: currentRange === 'hour' ? 3 : 0 
                    }]
                },
                options: commonOptions
            });

            const ctxHum = document.getElementById('humChart').getContext('2d');
            if (humChart) humChart.destroy();
            humChart = new Chart(ctxHum, {
                type: 'line',
                data: {
                    labels: times,
                    datasets: [
                        { label: 'Humidity (%)', data: hums, borderColor: '#36a2eb', borderWidth: 2, yAxisID: 'y', pointRadius: 0 },
                        { label: 'Air Quality (kOhm)', data: gases, borderColor: '#ffcd56', borderWidth: 2, yAxisID: 'y1', pointRadius: 0 }
                    ]
                },
                options: {
                    ...commonOptions,
                    scales: {
                        ...commonOptions.scales,
                        y: { ...commonOptions.scales.y, position: 'left', title: {display: true, text: '%'} },
                        y1: { position: 'right', grid: {drawOnChartArea: false}, title: {display: true, text: 'kOhm', color: '#ffcd56'}, ticks: {color: '#ffcd56'} }
                    }
                }
            });

        } catch (err) { console.error(err); }
    }

    // Init
    loadDevices();
    setInterval(loadData, 30000); 
</script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, use_12h=config.TIME_FORMAT_12H)

# NEW: API to list all devices
@app.route('/api/devices')
def get_devices():
    conn = get_db_connection()
    # Find all distinct device_ids
    devices = conn.execute("SELECT DISTINCT device_id FROM measurements WHERE device_id IS NOT NULL").fetchall()
    conn.close()
    device_list = [d['device_id'] for d in devices]
    return jsonify(device_list)

@app.route('/api/history')
def get_history():
    time_range = request.args.get('range', 'day')
    device_id = request.args.get('device_id') # Filter by device
    
    conn = get_db_connection()
    
    # Base WHERE clause
    where_clause = "WHERE 1=1"
    params = []
    
    # Add device filter
    if device_id:
        where_clause += " AND device_id = ?"
        params.append(device_id)
        
    # Time logic
    time_filter = ""
    if time_range == 'hour': time_filter = "AND timestamp >= datetime('now', '-1 hour')"
    elif time_range == 'day': time_filter = "AND timestamp >= datetime('now', '-24 hours')"
    elif time_range == 'week': time_filter = "AND timestamp >= datetime('now', '-7 days')"
    elif time_range == 'month': time_filter = "AND timestamp >= datetime('now', '-1 month')"
    
    where_clause += f" {time_filter}"

    # Build Query based on range (Aggregation)
    query = ""
    if time_range in ['week', 'month']:
        # Grouped Query
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
        # Full Resolution Query
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
        device_id = request.form.get('device_id', 'unknown') # Default to 'unknown' if missing
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
