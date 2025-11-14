import network
import socket
import random
from time import sleep
from machine import Pin
import sys

# CONFIGURA TU RED WIFI
ssid = 'raze'      # <-- cámbialo
password = 'armandocode'     # <-- cámbialo

# LED integrado (normalmente GPIO 2)
led = Pin(2, Pin.OUT)

def webpage(state, temperature, random_value):
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
                width: 200px;
                padding: 10px;
                margin: 10px;
                border-radius: 5px;
                text-decoration: none;
                color: white;
            }}
            .on {{ background-color: #4CAF50; }}
            .off {{ background-color: #f44336; }}
            .rand {{ background-color: #c0392b; }}
        </style>
    </head>
    <body>
        <h1>Control de LED</h1>
        <a class="button on" href="/lighton?">Encender luz LED</a>
        <a class="button off" href="/lightoff?">Apagar luz LED</a>
        <p>El LED esta: <strong>{state}</strong></p>
        
        <h2>Obtener nuevo valor aleatorio</h2>
        <a class="button rand" href="/random?">Obtener aleatorio</a>
        <p>Valor obtenido: <strong>{random_value}</strong></p>

        <h2>Resumen final</h2>
        <p>El LED esta: <strong>{state}</strong></p>
        <p>La Temperatura es: <strong>{temperature:.2f}</strong> °C</p>
        <p>Valor obtenido: <strong>{random_value}</strong></p>
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
        print('\nConectado a WiFi')
        print('IP:', wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
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
    state = 'OFF'
    led.value(0)
    random_value = 0
    temperature = random.uniform(25.0, 35.0)  # simula temperatura

    while True:
        client, addr = connection.accept()
        print('Cliente conectado desde', addr)
        request = client.recv(1024)
        request = str(request)

        if '/lighton?' in request:
            led.value(1)
            state = 'ON'
        elif '/lightoff?' in request:
            led.value(0)
            state = 'OFF'
        elif '/random?' in request:
            random_value = random.randint(0, 100)
            temperature = random.uniform(25.0, 35.0)

        html = webpage(state, temperature, random_value)
        client.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        client.send(html)
        client.close()


try:
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except Exception as e:
    print("Error del servidor:", e)
    sys.exit()
