from flask import Flask, request, jsonify, render_template_string
import sqlite3
import datetime
# NEW: Import Configuration
import config 


app = Flask(__name__)


# --- DATABASE ---
def get_db_connection():
    # Access via config.DB_NAME
    conn = sqlite3.connect(config.DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS measurements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  temperature REAL, 
                  humidity REAL, 
                  pressure REAL, 
                  gas_resistance REAL)''')
    conn.commit()
    conn.close()


init_db()


# --- HTML TEMPLATE (Frontend) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IoT Server Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #1a1a1a; color: #eee; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #03a9f4; text-align: center; }
        .chart-container { 
            background: #2a2a2a; 
            border-radius: 12px; 
            padding: 15px; 
            margin-bottom: 20px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            height: 300px;
        }
        .stats-row { display: flex; justify-content: space-around; margin-bottom: 20px; flex-wrap: wrap; }
        .card { background: #333; padding: 15px; border-radius: 8px; text-align: center; width: 140px; margin: 5px; border-top: 3px solid #777; }
        .val { font-size: 1.8rem; font-weight: bold; }
        .label { color: #aaa; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Server History</h1>
        
        <div class="stats-row">
            <div class="card" style="border-color: #ff6384">
                <div class="label">Temperature</div>
                <div class="val" id="cur-temp">--</div>
            </div>
            <div class="card" style="border-color: #36a2eb">
                <div class="label">Humidity</div>
                <div class="val" id="cur-hum">--</div>
            </div>
            <div class="card" style="border-color: #4bc0c0">
                <div class="label">Pressure</div>
                <div class="val" id="cur-pres">--</div>
            </div>
             <div class="card" style="border-color: #ffcd56">
                <div class="label">Gas (kOhm)</div>
                <div class="val" id="cur-gas">--</div>
            </div>
        </div>


        <div class="chart-container">
            <canvas id="tempChart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="humChart"></canvas>
        </div>
    </div>


<script>
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                type: 'time',
                time: { unit: 'minute', displayFormats: { minute: 'HH:mm' } },
                grid: { color: '#444' },
                ticks: { color: '#aaa' }
            },
            y: {
                grid: { color: '#444' },
                ticks: { color: '#aaa' }
            }
        },
        plugins: { legend: { labels: { color: '#eee' } } }
    };


    let tempChart, humChart;


    async function loadData() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            const times = data.map(d => new Date(d.timestamp));
            const temps = data.map(d => d.temperature);
            const hums = data.map(d => d.humidity);
            const press = data.map(d => d.pressure);
            const gases = data.map(d => d.gas_resistance / 1000.0); 


            if (data.length > 0) {
                const last = data[data.length - 1];
                document.getElementById('cur-temp').innerText = last.temperature.toFixed(1) + " °C";
                document.getElementById('cur-hum').innerText = last.humidity.toFixed(0) + " %";
                document.getElementById('cur-pres').innerText = last.pressure.toFixed(0) + " hPa";
                document.getElementById('cur-gas').innerText = (last.gas_resistance / 1000).toFixed(1);
            }


            const ctxTemp = document.getElementById('tempChart').getContext('2d');
            if (tempChart) tempChart.destroy();
            tempChart = new Chart(ctxTemp, {
                type: 'line',
                data: {
                    labels: times,
                    datasets: [{
                        label: 'Temperature (°C)',
                        data: temps,
                        borderColor: '#ff6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
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
                        {
                            label: 'Humidity (%)',
                            data: hums,
                            borderColor: '#36a2eb',
                            borderWidth: 2,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Air Quality (kOhm)',
                            data: gases,
                            borderColor: '#ffcd56',
                            borderWidth: 2,
                            yAxisID: 'y1'
                        }
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


        } catch (err) {
            console.error("Error loading data:", err);
        }
    }


    loadData();
    setInterval(loadData, 30000); 
</script>
</body>
</html>
"""


# --- ROUTES ---


@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/history')
def get_history():
    # Fetch last 50 entries
    conn = get_db_connection()
    measurements = conn.execute('SELECT * FROM (SELECT * FROM measurements ORDER BY id DESC LIMIT 50) ORDER BY id ASC').fetchall()
    conn.close()
    
    data = []
    for m in measurements:
        data.append({
            "timestamp": m['timestamp'], 
            "temperature": m['temperature'],
            "humidity": m['humidity'],
            "pressure": m['pressure'],
            "gas_resistance": m['gas_resistance']
        })
    return jsonify(data)


@app.route('/post-data', methods=['POST'])
def post_data():
    received_key = request.form.get('api_key')
    
    # Access via config.API_KEY
    if received_key != config.API_KEY:
        return jsonify({"status": "error", "message": "Invalid API Key"}), 403


    try:
        temp = float(request.form.get('temperature'))
        hum = float(request.form.get('humidity'))
        pres = float(request.form.get('pressure'))
        gas = float(request.form.get('gas'))
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO measurements (temperature, humidity, pressure, gas_resistance) VALUES (?, ?, ?, ?)",
                  (temp, hum, pres, gas))
        conn.commit()
        conn.close()
        
        print(f"[{datetime.datetime.now()}] Saved: {temp}°C")
        return jsonify({"status": "success"}), 200


    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == '__main__':
    # Access via config.HOST, config.PORT, config.DEBUG
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
