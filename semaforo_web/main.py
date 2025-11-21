import network
import socket
import time
import random
from machine import Pin, PWM

# WIFI
ssid = "raze"
password = "armandocode"

# LEDs físicos
led_red = Pin(12, Pin.OUT)
led_yellow = Pin(14, Pin.OUT)
led_green = Pin(13, Pin.OUT)

# Peatones
led_walk = Pin(25, Pin.OUT)
led_stop = Pin(26, Pin.OUT)

# Buzzer
buzzer = PWM(Pin(27))
buzzer.duty(0)

# Estado
state = "red"
timer = 10

# Dashboard suave
last_temp = 25
last_hum = 50
last_update_env = time.ticks_ms()

def smooth_value(current, target_range=2):
    return current + random.randint(-target_range, target_range)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(0.3)
    print("Conectado:", wlan.ifconfig())

connect_wifi()

# HTML nuevo estilo “full page semáforo”
html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Semáforo ESP32</title>
<style>
body {
    font-family: Arial;
    text-align: center;
    margin: 0;
    padding: 0;
    transition: background 0.5s;
}

.icon {
    font-size: 150px;
    margin-top: 40px;
}

.timer {
    font-size: 120px;
    font-weight: bold;
    margin-top: -20px;
}

.dashboard {
    background: white;
    padding: 15px;
    width: 250px;
    margin: 30px auto;
    border-radius: 10px;
    box-shadow: 0 0 15px #aaa;
    font-size: 18px;
}

</style>
<script>
function update() {
    fetch('/state').then(r => r.json()).then(data => {

        // Fondo según el estado
        if(data.state == "red")   document.body.style.background = "#ff8a8a";
        if(data.state == "yellow") document.body.style.background = "#ffe97a";
        if(data.state == "green") document.body.style.background = "#7aff8a";

        // Ícono
        document.getElementById("icon").innerText =
            data.state == "green" ? "🚶" : "🚗";

        // Timer gigante
        document.getElementById("timer").innerText = data.timer;

        // Dashboard
        document.getElementById("temp").innerText = data.temp;
        document.getElementById("hum").innerText = data.hum;

        // Parpadeo último segundo
        if(data.timer == 1){
            document.body.style.opacity =
                (document.body.style.opacity == "0.5" ? "1" : "0.5");
        } else {
            document.body.style.opacity = "1";
        }
    });
}
setInterval(update, 500);
</script>
</head>

<body>

<div id="icon" class="icon">🚗</div>
<div id="timer" class="timer">0</div>

<div class="dashboard">
    <h3>Información</h3>
    Temp: <span id="temp">0</span>°C<br>
    Humedad: <span id="hum">0</span>%
</div>

</body>
</html>
"""

# Servidor
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(5)
print("Servidor listo")

# Actualización de LEDs físicos
def update_lights():
    global state
    led_red.value(state == "red")
    led_yellow.value(state == "yellow")
    led_green.value(state == "green")

    led_walk.value(state == "green")
    led_stop.value(state != "green")

    if state == "red":
        buzzer.freq(900)
        buzzer.duty(200)
    else:
        buzzer.duty(0)

# Ciclos de tiempo
last_change = time.ticks_ms()

while True:

    now = time.ticks_ms()

    # Cambio de semáforo
    if time.ticks_diff(now, last_change) >= 1000:
        timer -= 1

        if timer <= 0:
            if state == "red":
                state = "green"
                timer = 8
            elif state == "green":
                state = "yellow"
                timer = 3
            elif state == "yellow":
                state = "red"
                timer = 10

        update_lights()
        last_change = now

    # Dashboard cada 2 segundos
    if time.ticks_diff(now, last_update_env) >= 2000:
        last_temp = smooth_value(last_temp, target_range=1)
        last_hum = smooth_value(last_hum, target_range=1)
        last_update_env = now

    # Servidor web
    try:
        cl, addr = s.accept()
        req = cl.recv(1024).decode()

        if "GET /state" in req:
            response = (
                '{"state":"%s","timer":%d,"temp":%d,"hum":%d}'
                % (state, timer, last_temp, last_hum)
            )
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            cl.send(response)
        else:
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            cl.send(html)

        cl.close()
    except:
        pass
