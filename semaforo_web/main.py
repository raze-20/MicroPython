import network
import socket
import time
import random
from machine import Pin

# -----------------------------------
# WIFI
# -----------------------------------
ssid = "raze"
password = "armandocode"

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while not station.isconnected():
    time.sleep(0.2)

print("Conectado:", station.ifconfig())

# -----------------------------------
# SEMAFORO FISICO
# -----------------------------------
red_led = Pin(12, Pin.OUT)
yellow_led = Pin(13, Pin.OUT)
green_led = Pin(14, Pin.OUT)

traffic_state = 0
last_change = time.ticks_ms()

# -----------------------------------
# SENSOR SIMULADO
# -----------------------------------
temperature = 0
humidity = 0

def update_sensors():
    global temperature, humidity
    temperature = random.uniform(20, 30)
    humidity = random.uniform(40, 60)

# -----------------------------------
# SEMAFORO AUTOMATICO
# -----------------------------------
def update_traffic():
    global traffic_state, last_change
    now = time.ticks_ms()

    if time.ticks_diff(now, last_change) > 3000:
        traffic_state = (traffic_state + 1) % 3
        last_change = now

    red_led.value(1 if traffic_state == 0 else 0)
    yellow_led.value(1 if traffic_state == 1 else 0)
    green_led.value(1 if traffic_state == 2 else 0)

# -----------------------------------
# PAGINA
# -----------------------------------
def webpage():
    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="2">

    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #1d1d1f;
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #f2f2f7;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .card {{
            margin-top: 40px;
            width: 300px;
            background: #2c2c2e;
            border-radius: 28px;
            padding: 25px 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.35);
        }}

        .traffic {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 22px;
            padding: 25px 20px;
            border-radius: 24px;
            background: #3a3a3c;
            box-shadow: inset 0 0 25px rgba(0,0,0,0.45);
        }}

        .light {{
            width: 75px;
            height: 75px;
            border-radius: 50%;
            background: #555;
            transition: 0.3s;
            box-shadow: 0 0 15px rgba(0,0,0,0.6);
        }}

        #red {{
            background: {"#ff453a" if traffic_state == 0 else "#3a3a3c"};
            box-shadow: {"0 0 25px #ff453a88" if traffic_state == 0 else "none"};
        }}

        #yellow {{
            background: {"#ffd60a" if traffic_state == 1 else "#3a3a3c"};
            box-shadow: {"0 0 25px #ffd60a88" if traffic_state == 1 else "none"};
        }}

        #green {{
            background: {"#32d74b" if traffic_state == 2 else "#3a3a3c"};
            box-shadow: {"0 0 25px #32d74b88" if traffic_state == 2 else "none"};
        }}

        .data {{
            margin-top: 30px;
            text-align: center;
            font-size: 20px;
            font-weight: 300;
            letter-spacing: 0.5px;
        }}

        .value {{
            font-size: 26px;
            font-weight: 600;
            margin-top: 6px;
        }}
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
                <div class="value">{temperature:.1f} °C</div>

                <p style="margin-top:20px;">Humedad</p>
                <div class="value">{humidity:.1f} %</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# -----------------------------------
# SERVIDOR WEB
# -----------------------------------
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(5)
print("Servidor listo en:", addr)

# -----------------------------------
# LOOP
# -----------------------------------
while True:
    update_traffic()
    update_sensors()

    try:
        client, addr = s.accept()
        request = client.recv(1024)
        response = webpage()
        client.send("HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n")
        client.send(response)
        client.close()
    except:
        pass

    time.sleep(0.1)
