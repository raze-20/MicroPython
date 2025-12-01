import network
import socket
import time
import random
import json
from machine import Pin

# -----------------------------------
# 1. CONFIGURACIÓN WIFI
# -----------------------------------
ssid = "..."
password = "..."

print("Conectando a WiFi...")
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while not station.isconnected():
    time.sleep(0.1)

ip_address = station.ifconfig()[0]
print(f"Conectado: {ip_address}")

# -----------------------------------
# HARDWARE
# -----------------------------------
red_led = Pin(12, Pin.OUT)
yellow_led = Pin(13, Pin.OUT)
green_led = Pin(14, Pin.OUT)

# Estados: 0 = ROJO, 1 = AMARILLO, 2 = VERDE
traffic_state = 0 
last_traffic_change = time.ticks_ms()
last_sensor_change = time.ticks_ms()

# Variables sensores
temperature = 25.0
humidity = 50.0

# -----------------------------------
# LÓGICA DEL SISTEMA
# -----------------------------------

def update_sensors():
    global temperature, humidity, last_sensor_change
    now = time.ticks_ms()
    
    # Actualiza sensores cada 5 segundos
    if time.ticks_diff(now, last_sensor_change) > 5000:
        temperature = random.uniform(20, 28)
        humidity = random.uniform(40, 60)
        last_sensor_change = now

def update_traffic():
    global traffic_state, last_traffic_change
    now = time.ticks_ms()
    diff = time.ticks_diff(now, last_traffic_change)

    # --- LÓGICA DE SEMÁFORO REAL (Proporcional) ---
    
    # SI ESTÁ EN ROJO (0)
    if traffic_state == 0:
        # El rojo dura bastante (ej. 4 segundos) para detener el tráfico
        if diff > 4000:
            traffic_state = 2 # Del Rojo pasa directo al Verde
            last_traffic_change = now

    # SI ESTÁ EN VERDE (2)
    elif traffic_state == 2:
        # El verde dura bastante (ej. 4 segundos) para avanzar
        if diff > 4000:
            traffic_state = 1 # Del Verde pasa al Amarillo (precaución)
            last_traffic_change = now

    # SI ESTÁ EN AMARILLO (1)
    elif traffic_state == 1:
        # El amarillo dura POCO (ej. 1.5 segundos) solo aviso
        if diff > 1500:
            traffic_state = 0 # Del Amarillo pasa al Rojo
            last_traffic_change = now

    # Actualizar Leds Físicos
    red_led.value(1 if traffic_state == 0 else 0)
    yellow_led.value(1 if traffic_state == 1 else 0)
    green_led.value(1 if traffic_state == 2 else 0)

# -----------------------------------
# HTML + JAVASCRIPT
# -----------------------------------
def get_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8"> <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { margin: 0; padding: 0; background: #1d1d1f; font-family: sans-serif; color: #f2f2f7; display: flex; flex-direction: column; align-items: center; }
        .card { margin-top: 40px; width: 300px; background: #2c2c2e; border-radius: 28px; padding: 25px 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.35); }
        .traffic { display: flex; flex-direction: column; align-items: center; gap: 22px; padding: 25px 20px; border-radius: 24px; background: #3a3a3c; box-shadow: inset 0 0 25px rgba(0,0,0,0.45); }
        
        /* Orden visual de los focos */
        .light { width: 75px; height: 75px; border-radius: 50%; background: #3a3a3c; transition: 0.2s; box-shadow: none; }
        
        .on-red { background: #ff453a !important; box-shadow: 0 0 25px #ff453a88 !important; }
        .on-yellow { background: #ffd60a !important; box-shadow: 0 0 25px #ffd60a88 !important; }
        .on-green { background: #32d74b !important; box-shadow: 0 0 25px #32d74b88 !important; }

        .data { margin-top: 30px; text-align: center; font-size: 20px; font-weight: 300; }
        .value { font-size: 26px; font-weight: 600; margin-top: 6px; }
    </style>
    </head>
    <body>
        <div class="card">
            <div class="traffic">
 
                <div class="light" id="red"></div>
                <div class="light" id="yellow"></div>
                <div class="light" id="green"></div>
            </div>
            <div class="data">
                <p>Temperatura</p>
                <div class="value" id="val-temp">-- &deg;C</div>
                <p style="margin-top:20px;">Humedad</p>
                <div class="value" id="val-hum">-- %</div>
            </div>
        </div>

        <script>
            setInterval(() => {
                fetch('/data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('val-temp').innerHTML = data.temp.toFixed(1) + " &deg;C";
                    document.getElementById('val-hum').innerText = data.hum.toFixed(1) + " %";

                    const s = data.state;
                    const r = document.getElementById('red');
                    const y = document.getElementById('yellow');
                    const g = document.getElementById('green');

                    r.className = 'light';
                    y.className = 'light';
                    g.className = 'light';

                    if(s === 0) r.classList.add('on-red');
                    if(s === 1) y.classList.add('on-yellow');
                    if(s === 2) g.classList.add('on-green');
                })
                .catch(err => console.log(err));
            }, 200);
        </script>
    </body>
    </html>
    """

# -----------------------------------
# SERVIDOR WEB
# -----------------------------------
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(5)
s.setblocking(False)

print(f"Servidor listo en: http://{ip_address}")

# -----------------------------------
# LOOP PRINCIPAL
# -----------------------------------
while True:
    update_traffic()
    update_sensors()

    try:
        conn, addr = s.accept()
        conn.settimeout(3.0)
        request = conn.recv(1024)
        req_str = str(request)
        
        if '/data' in req_str:
            response_json = json.dumps({
                "state": traffic_state,
                "temp": temperature,
                "hum": humidity
            })
            header = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            conn.send(header)
            conn.send(response_json)
        else:
            response_html = get_html()
            header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            conn.send(header)
            conn.send(response_html)
            
        conn.close()
    except OSError:
        pass
        
    time.sleep(0.05)