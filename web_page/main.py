import network
import socket
import random
from time import sleep
from machine import Pin
import sys
import dht

# CONFIGURA TU RED WIFI
ssid = "raze"
password = "armandocode"

# PINS
led_internal = Pin(2, Pin.OUT)
led_blue = Pin(14, Pin.OUT)
led_red = Pin(12, Pin.OUT)
led_green = Pin(13, Pin.OUT)
buzzer = Pin(27, Pin.OUT)

# SENSOR
sensor = dht.DHT22(Pin(4))  # Cambia a DHT11 si usas ese modelo

# ------------------------- HTML UI -------------------------

def webpage(states, temp_int, temp_ext, hum_ext, delta, random_value):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial;
                background: #e6e6e6;
                text-align: center;
                margin: 0;
            }}

            h1 {{
                background: #2c3e50;
                color: white;
                padding: 18px;
                margin: 0;
            }}

            .container {{
                width: 95%;
                max-width: 900px;
                margin: auto;
            }}

            .card {{
                background: white;
                padding: 15px;
                margin: 15px auto;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }}

            .btn {{
                padding: 10px 15px;
                border-radius: 6px;
                text-decoration: none;
                margin: 5px;
                display: inline-block;
                color: white;
            }}

            .on {{
                background: #27ae60;
            }}
            .off {{
                background: #c0392b;
            }}

            .title {{
                font-size: 22px;
                margin-bottom: 5px;
                font-weight: bold;
            }}

            .state {{
                font-size: 18px;
                margin: 6px 0;
            }}

        </style>
    </head>
    <body>

        <h1>Dashboard de Control ESP32</h1>

        <div class="container">

            <div class="card">
                <div class="title">Control Global</div>
                <a class="btn on" href="/allon?">Encender Todo</a>
                <a class="btn off" href="/alloff?">Apagar Todo</a>
            </div>

            <div class="card">
                <div class="title">LED Interno</div>
                <p class="state">Estado: {states['internal']}</p>
                <a class="btn on" href="/internal_on?">Encender</a>
                <a class="btn off" href="/internal_off?">Apagar</a>
            </div>

            <div class="card">
                <div class="title">LED Azul</div>
                <p class="state">Estado: {states['blue']}</p>
                <a class="btn on" href="/blue_on?">Encender</a>
                <a class="btn off" href="/blue_off?">Apagar</a>
            </div>

            <div class="card">
                <div class="title">LED Rojo</div>
                <p class="state">Estado: {states['red']}</p>
                <a class="btn on" href="/red_on?">Encender</a>
                <a class="btn off" href="/red_off?">Apagar</a>
            </div>

            <div class="card">
                <div class="title">LED Verde</div>
                <p class="state">Estado: {states['green']}</p>
                <a class="btn on" href="/green_on?">Encender</a>
                <a class="btn off" href="/green_off?">Apagar</a>
            </div>

            <div class="card">
                <div class="title">Buzzer</div>
                <p class="state">Estado: {states['buzzer']}</p>
                <a class="btn on" href="/buzzer_on?">Encender</a>
                <a class="btn off" href="/buzzer_off?">Apagar</a>
            </div>

            <div class="card">
                <div class="title">Sensor DHT</div>
                <p>Temperatura interna: <strong>{temp_int:.2f} °C</strong></p>
                <p>Temperatura externa: <strong>{temp_ext if temp_ext is not None else "N/A"}</strong></p>
                <p>Humedad: <strong>{hum_ext if hum_ext is not None else "N/A"}%</strong></p>
                <p>Diferencia: <strong>{delta if delta is not None else "N/A"} °C</strong></p>
            </div>

            <div class="card">
                <div class="title">Valor Aleatorio</div>
                <p><strong>{random_value}</strong></p>
                <a class="btn on" href="/random?">Generar</a>
            </div>

        </div>

    </body>
    </html>
    """
    return html


# ------------------------- RED -------------------------

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    print("Conectando a WiFi...")

    for _ in range(20):
        if wlan.isconnected():
            break
        print(".", end="")
        sleep(1)

    if not wlan.isconnected():
        print("Error conectando")
        sys.exit()

    print("\nIP:", wlan.ifconfig()[0])
    return wlan.ifconfig()[0]


def open_socket(ip):
    sock = socket.socket()
    sock.bind((ip, 80))
    sock.listen(1)
    print("Servidor listo en", ip)
    return sock


# ------------------------- SERVIDOR -------------------------

def serve(sock):
    states = {
        "internal": "OFF",
        "blue": "OFF",
        "red": "OFF",
        "green": "OFF",
        "buzzer": "OFF"
    }

    # Inicializar valores
    for pin in [led_internal, led_blue, led_red, led_green, buzzer]:
        pin.value(0)

    temp_int = random.uniform(25, 35)
    random_value = 0

    while True:

        client, addr = sock.accept()
        print("Cliente:", addr)
        request = client.recv(1024).decode()

        # ------------------- RUTAS -------------------

        if "/internal_on?" in request:
            led_internal.value(1); states["internal"] = "ON"
        if "/internal_off?" in request:
            led_internal.value(0); states["internal"] = "OFF"

        if "/blue_on?" in request:
            led_blue.value(1); states["blue"] = "ON"
        if "/blue_off?" in request:
            led_blue.value(0); states["blue"] = "OFF"

        if "/red_on?" in request:
            led_red.value(1); states["red"] = "ON"
        if "/red_off?" in request:
            led_red.value(0); states["red"] = "OFF"

        if "/green_on?" in request:
            led_green.value(1); states["green"] = "ON"
        if "/green_off?" in request:
            led_green.value(0); states["green"] = "OFF"

        if "/buzzer_on?" in request:
            buzzer.value(1); states["buzzer"] = "ON"
        if "/buzzer_off?" in request:
            buzzer.value(0); states["buzzer"] = "OFF"

        if "/allon?" in request:
            for p in [led_internal, led_blue, led_red, led_green, buzzer]:
                p.value(1)
            for k in states:
                states[k] = "ON"

        if "/alloff?" in request:
            for p in [led_internal, led_blue, led_red, led_green, buzzer]:
                p.value(0)
            for k in states:
                states[k] = "OFF"

        if "/random?" in request:
            random_value = random.randint(0, 100)
            temp_int = random.uniform(25, 35)

        # ------------------- SENSOR -------------------

        try:
            sensor.measure()
            temp_ext = sensor.temperature()
            hum_ext = sensor.humidity()
            delta = round(abs(temp_int - temp_ext), 2)
        except:
            temp_ext = None
            hum_ext = None
            delta = None

        # ------------------- RESPUESTA -------------------

        html = webpage(states, temp_int, temp_ext, hum_ext, delta, random_value)
        client.send("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n")
        client.send(html)
        client.close()


# ------------------------- MAIN -------------------------

try:
    ip = connect()
    sock = open_socket(ip)
    serve(sock)
except Exception as e:
    print("Error:", e)
    sys.exit()
