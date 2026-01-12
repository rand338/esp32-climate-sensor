# config.py

# API Key for the ESP32 (Must match config.h in the sketch)
API_KEY = "MySecretIoTKey123"

# Name of the SQLite database file
DB_NAME = "climate.db"

# Server Settings
HOST = '0.0.0.0'  # 0.0.0.0 = Accessible within the network
PORT = 5000
DEBUG = True      # True for development, False for production
