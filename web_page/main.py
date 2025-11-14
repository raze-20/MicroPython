import network
import socket
import random
from time import sleep
from machine import Pin
import sys
import dht

# CONFIGURA TU RED WIFI
ssid = 'raze'            # <-- cámbialo si hace falta
password = 'armandocode' # <-- cámbialo si hace falta

# PINS - ajusta según tu conexión física
led = Pin(2, Pin.OUT)      # LED interno del ESP32
led_1 = Pin(14, Pin.OUT)   # LED Azul (por ejemplo)
led_2 = Pin(12, Pin.OUT)   # LED Rojo (por ejemplo)
led_3 = Pin(13, Pin.OUT)   # LED Verde (por ejemplo)
buzzer = Pin(27, Pin.OUT)  # Buzzer

# Sensor DHT (DHT22 o DHT11 según el que uses)
dht_pin = Pin(4)
sensor = dht.DHT22(dht_pin)  # Cambia a DHT11 si usas ese modelo

def webpage(state_0, state_1, state_2, state_3, state_buzzer,
            temp_internal, temp_ext, hum_ext, delta_temp, random_value):
    # HTML dinámico
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Servidor ESP32</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f7f7f7; text-align: center; }}
            h1 {{ color: #007bff; }}
            .button {{
                display: inline-block;
                width: 180px;
                padding: 10px;
                margin: 6px;
                border-radius: 5px;
                text-decoration: none;
                color: white;
            }}
            .on {{ background-color: #4CAF50; }}
            .off {{ background-color: #f44336; }}
            .rand {{ background-color: #c0392b; }}
            .info {{ background-color: #2d3436; padding: 10px; color: white; display: inline-block; border-radius: 6px; }}
            .section {{ margin: 18px 0; }}
        </style>
    </head>
    <body>
        <h1>Control de LEDs y Sensor</h1>

        <div class="section">
            <h2>Control global</h2>
            <a class="button on" href="/allon?">Encender todos</a>
            <a class="button off" href="/alloff?">Apagar todos</a>
        </div>

        <div class="section">
            <h2>LED interno</h2>
            <a class="button on" href="/lighton_0?">Encender</a>
            <a class="button off" href="/lightoff_0?">Apagar</a>
            <p>Estado: <strong>{state_0}</strong></p>
        </div>

        <div class="section">
            <h2>LED 1 (Azul)</h2>
            <a class="button on" href="/lighton_1?">Encender</a>
            <a class="button off" href="/lightoff_1?">Apagar</a>
            <p>Estado: <strong>{state_1}</strong></p>
        </div>

        <div class="section">
            <h2>LED 2 (Rojo)</h2>
            <a class="button on" href="/lighton_2?">Encender</a>
            <a class="button off" href="/lightoff_2?">Apagar</a>
            <p>Estado: <strong>{state_2}</strong></p>
        </div>

        <div class="section">
            <h2>LED 3 (Verde)</h2>
            <a class="button on" href="/lighton_3?">Encender</a>
            <a class="button off" href="/lightoff_3?">Apagar</a>
            <p>Estado: <strong>{state_3}</strong></p>
        </div>

        <div class="section">
            <h2>Buzzer</h2>
            <a class="button on" href="/buzzeron?">Encender Buzzer</a>
            <a class="button off" href="/buzzeroff?">Apagar Buzzer</a>
            <p>Estado: <strong>{state_buzzer}</strong></p>
        </div>

        <div class="section">
            <h2>Sensor (DHT)</h2>
            <div class="info">
                <p>Temp interna (simulada): <strong>{temp_internal:.2f} °C</strong></p>
                <p>Temp externa (sensor): <strong>{temp_ext if temp_ext is not None else 'N/A'}</strong></p>
                <p>Humedad externa: <strong>{hum_ext if hum_ext is not None else 'N/A'}</strong></p>
                <p>Diferencia: <strong>{delta_temp if delta_temp is not None else 'N/A'}</strong> °C</p>
            </div>
        </div>

        <div class="section">
            <h2>Valor aleatorio</h2>
            <a class="button rand" href="/random?">Generar aleatorio</a>
            <p>Valor: <strong>{random_value}</strong></p>
        </div>

        <hr>
        <p style="font-size:smaller;color:gray;">ESP32 - MicroPython</p>
    </body>
    </html>
    """
    return html

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print('Conectando a la red...')
    for _ in range(15):
        if wlan.isconnected():
            break
        print('.', end='')
        sleep(1)

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print('\nConectado a WiFi')
        print('IP:', ip)
        return ip
    else:
        print('\nError: no se pudo conectar')
        sys.exit()

def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    print("Servidor listo en:", ip)
    return connection

def serve(connection):
    # Estados iniciales
    state_0 = 'OFF'
    state_1 = 'OFF'
    state_2 = 'OFF'
    state_3 = 'OFF'
    state_buzzer = 'OFF'

    # Inicializa salidas
    led.value(0)
    led_1.value(0)
    led_2.value(0)
    led_3.value(0)
    buzzer.value(0)

    random_value = 0
    temp_internal = random.uniform(25.0, 35.0)  # temperatura interna simulada

    while True:
        client, addr = connection.accept()
        print('Cliente conectado desde', addr)
        try:
            request = client.recv(2048)
            request = str(request)
            print('Solicitud:', request.split('\\r\\n')[0])
        except Exception as e:
            print('Error leyendo la solicitud:', e)
            client.close()
            continue

        # RUTAS - manejo de acciones
        if '/lighton_0?' in request:
            led.value(1); state_0 = 'ON'
        elif '/lightoff_0?' in request:
            led.value(0); state_0 = 'OFF'

        elif '/lighton_1?' in request:
            led_1.value(1); state_1 = 'ON'
        elif '/lightoff_1?' in request:
            led_1.value(0); state_1 = 'OFF'

        elif '/lighton_2?' in request:
            led_2.value(1); state_2 = 'ON'
        elif '/lightoff_2?' in request:
            led_2.value(0); state_2 = 'OFF'

        elif '/lighton_3?' in request:
            led_3.value(1); state_3 = 'ON'
        elif '/lightoff_3?' in request:
            led_3.value(0); state_3 = 'OFF'

        elif '/allon?' in request:
            led.value(1); led_1.value(1); led_2.value(1); led_3.value(1)
            state_0 = state_1 = state_2 = state_3 = 'ON'
        elif '/alloff?' in request:
            led.value(0); led_1.value(0); led_2.value(0); led_3.value(0)
            state_0 = state_1 = state_2 = state_3 = 'OFF'

        elif '/buzzeron?' in request:
            buzzer.value(1); state_buzzer = 'ON'
        elif '/buzzeroff?' in request:
            buzzer.value(0); state_buzzer = 'OFF'

        elif '/random?' in request:
            random_value = random.randint(0, 100)
            temp_internal = random.uniform(25.0, 35.0)

        # Lectura del sensor DHT (manejo de errores)
        temp_ext = None
        hum_ext = None
        delta_temp = None
        try:
            sensor.measure()
            temp_ext = sensor.temperature()
            hum_ext = sensor.humidity()
            # calcular diferencia si tenemos temp interna y externa
            if temp_ext is not None:
                delta_temp = round(abs(temp_internal - float(temp_ext)), 2)
        except Exception as e:
            print('Error leyendo DHT:', e)
            # deja temp_ext/hum_ext como None para mostrar N/A en la web

        # Generar y enviar la respuesta
        try:
            html = webpage(state_0, state_1, state_2, state_3, state_buzzer,
                           temp_internal, temp_ext, hum_ext, delta_temp, random_value)
            client.send('HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n'.encode('utf-8'))
            client.send(html.encode('utf-8'))
        except Exception as e:
            print('Error enviando respuesta:', e)
        finally:
            client.close()

try:
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except Exception as e:
    print("Error del servidor:", e)
    sys.exit()
