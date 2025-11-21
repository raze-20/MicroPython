import network
import socket
import random
from time import sleep
from machine import Pin, ADC, PWM
import sys

# CONFIGURA TU RED WIFI
ssid = "raze"
password = "armandocode"

# LEDS
led_internal = Pin(2, Pin.OUT)
led_blue = Pin(14, Pin.OUT)
led_red = Pin(12, Pin.OUT)
led_green = Pin(13, Pin.OUT)

# SENSOR LM35 (pin ADC)
lm35 = ADC(Pin(34))
lm35.atten(ADC.ATTN_11DB)  # rango hasta ~3.3V

# LISTAS DE DATOS
temps_internal = []
temps_external = []
humidity = []

N = 10  # cantidad de muestras

# ---------------- TEMPERATURAS ----------------

def read_internal_temp():
    return random.uniform(25, 38)

def read_external_temp():
    # Lectura real LM35
    
    return random.uniform(25, 38)

def read_humidity():
    return random.uniform(20, 60)

def update_measurements():
    if len(temps_internal) >= N:
        temps_internal.pop(0)
    temps_internal.append(read_internal_temp())

    if len(temps_external) >= N:
        temps_external.pop(0)
    temps_external.append(read_external_temp())

    if len(humidity) >= N:
        humidity.pop(0)
    humidity.append(read_humidity())

def calc_avg(lst):
    if len(lst) == 0:
        return 0
    return sum(lst) / len(lst)

# ---------------- HTML ----------------

def table_html():
    rows = []

    for i in range(N):
        ti = f"{temps_internal[i]:.2f} °C" if i < len(temps_internal) else ""
        te = f"{temps_external[i]:.2f} °C" if i < len(temps_external) else ""
        hu = f"{humidity[i]:.2f} %" if i < len(humidity) else ""
        rows.append(f"<tr><td>{ti}</td><td>{te}</td><td>{hu}</td></tr>")

    avg_i = calc_avg(temps_internal)
    avg_e = calc_avg(temps_external)
    avg_h = calc_avg(humidity)

    diff = avg_i - avg_e if len(temps_internal) == N and len(temps_external) == N else 0

    rows.append(f"""
        <tr style='font-weight:bold; background:#ddd;'>
            <td>Promedio: {avg_i:.2f} °C</td>
            <td>Promedio: {avg_e:.2f} °C</td>
            <td>Promedio: {avg_h:.2f} %</td>
        </tr>
    """)

    rows.append(f"""
        <tr style='font-weight:bold; background:#ccc;'>
            <td colspan="3">Diferencia interna - externa: {diff:.2f} °C</td>
        </tr>
    """)

    return "".join(rows)

def webpage(states, random_value):
    update_measurements()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard ESP32</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial;
                background: #f2f2f2;
                text-align: center;
            }}
            h1 {{
                background: #2c3e50;
                color: white;
                padding: 15px;
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
                border-radius: 10px;
                box-shadow: 0 3px 8px rgba(0,0,0,0.2);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            table td, table th {{
                border: 1px solid #aaa;
                padding: 6px;
            }}
            .btn {{
                padding: 10px 15px;
                border-radius: 6px;
                text-decoration: none;
                margin: 5px;
                display: inline-block;
                color: white;
            }}
            .on {{ background: #27ae60; }}
            .off {{ background: #c0392b; }}
        </style>
    </head>

    <body>
        <h1>Dashboard de Control</h1>

        <div class="container">

            <div class="card">
                <h2>Control Global</h2>
                <a class="btn on" href="/allon?">Encender Todo</a>
                <a class="btn off" href="/alloff?">Apagar Todo</a>
            </div>

            <div class="card">
                <h2>Control Individual</h2>
                
                <p>LED Interno: {states['internal']}</p>
                <a class="btn on" href="/internal_on?">Encender</a>
                <a class="btn off" href="/internal_off?">Apagar</a>

                <p>LED Azul: {states['blue']}</p>
                <a class="btn on" href="/blue_on?">Encender</a>
                <a class="btn off" href="/blue_off?">Apagar</a>

                <p>LED Rojo: {states['red']}</p>
                <a class="btn on" href="/red_on?">Encender</a>
                <a class="btn off" href="/red_off?">Apagar</a>

                <p>LED Verde: {states['green']}</p>
                <a class="btn on" href="/green_on?">Encender</a>
                <a class="btn off" href="/green_off?">Apagar</a>

                <p>Buzzer: {states['buzzer']}</p>
                <a class="btn on" href="/buzzer_on?">Encender</a>
                <a class="btn off" href="/buzzer_off?">Apagar</a>
            </div>

            <div class="card">
                <h2>Lecturas</h2>
                <table>
                    <tr>
                        <th>Temp. Interna</th>
                        <th>Temp. Externa (LM35)</th>
                        <th>Humedad</th>
                    </tr>
                    {table_html()}
                </table>
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

# ---------------- RED ----------------

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)

    print("Conectando a WiFi...")
    for _ in range(20):
        if wlan.isconnected():
            break
        sleep(1)

    if not wlan.isconnected():
        print("Error conectando")
        return None

    ip = wlan.ifconfig()[0]
    print("IP:", ip)
    return ip

def open_socket(ip):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, 80))
    sock.listen(1)
    return sock

# ---------------- SERVIDOR ----------------

def serve(sock):
    states = {
        "internal": "OFF",
        "blue": "OFF",
        "red": "OFF",
        "green": "OFF",
        "buzzer": "OFF",
    }

    for p in [led_internal, led_blue, led_red, led_green]:
        p.value(0)

    buzzer_pwm = None
    random_value = 0

    while True:
        try:
            client, addr = sock.accept()
            client.settimeout(3.0)
            try:
                request = client.recv(2048)
                if not request:
                    client.close()
                    continue
                request = request.decode('utf-8', 'ignore')
            except Exception:
                client.close()
                continue

            # ------------ RUTAS ------------
            if "/allon?" in request:
                for p in [led_internal, led_blue, led_red, led_green]:
                    p.value(1)
                for k in states:
                    states[k] = "ON"

                if buzzer_pwm is None:
                    buzzer_pwm = PWM(Pin(27), freq=1500, duty=600)
                    sleep(0.25)
                    buzzer_pwm.deinit()
                    buzzer_pwm = None

            if "/alloff?" in request:
                for p in [led_internal, led_blue, led_red, led_green]:
                    p.value(0)
                for k in states:
                    states[k] = "OFF"
                if buzzer_pwm is not None:
                    buzzer_pwm.deinit()
                    buzzer_pwm = None
                states["buzzer"] = "OFF"

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
                if buzzer_pwm is None:
                    buzzer_pwm = PWM(Pin(27), freq=1500, duty=600)
                states["buzzer"] = "ON"

            if "/buzzer_off?" in request:
                if buzzer_pwm is not None:
                    buzzer_pwm.deinit()
                    buzzer_pwm = None
                states["buzzer"] = "OFF"

            if "/random?" in request:
                random_value = random.randint(1, 100)

            response = webpage(states, random_value)
            client.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            client.sendall(response)
            client.close()

        except Exception as e:
            try:
                client.close()
            except:
                pass
            print("Error:", e)

# ---------------- MAIN ---------------- 
ip = connect() 
if ip: 
    sock = open_socket(ip) 
    serve(sock) 
else: 
    print("No se pudo conectar a WiFi. Reinicia o revisa credenciales.")
