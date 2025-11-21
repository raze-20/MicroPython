# main.py -- Semáforo web + lectura DHT (MicroPython, ESP32)
import uasyncio as asyncio
import network
import socket
import ujson
from machine import Pin
import dht
import time

# --- CONFIG ---
SSID = "raze"
PASSWORD = "armandocode"

# PINES (ajusta si necesitas)
PIN_RED = 12
PIN_YELLOW = 13
PIN_GREEN = 14
PIN_DHT = 15  # DHT22 or DHT11 data pin

# DURACIONES modo automático (en segundos)
DUR_RED = 6
DUR_GREEN = 6
DUR_YELLOW = 2

# --- Hardware setup ---
led_red = Pin(PIN_RED, Pin.OUT)
led_yellow = Pin(PIN_YELLOW, Pin.OUT)
led_green = Pin(PIN_GREEN, Pin.OUT)
dht_sensor = dht.DHT22(Pin(PIN_DHT))  # si usas DHT11, cambia a dht.DHT11

# Estado compartido
state = {
    "mode": "auto",        # "auto" o "manual"
    "light": "red",        # "red","yellow","green"
    "temp": None,
    "hum": None,
    "last_update": None
}

# --- Utilities ---
def set_light(name):
    """Encender el LED físico correspondiente y apagar los otros"""
    state["light"] = name
    if name == "red":
        led_red.on(); led_yellow.off(); led_green.off()
    elif name == "yellow":
        led_red.off(); led_yellow.on(); led_green.off()
    elif name == "green":
        led_red.off(); led_yellow.off(); led_green.on()
    else:
        led_red.off(); led_yellow.off(); led_green.off()

# Start with red
set_light("red")

# --- WiFi connect ---
def connect_wifi(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        t0 = time.time()
        while not wlan.isconnected():
            if time.time() - t0 > timeout:
                raise RuntimeError("No se pudo conectar a WiFi")
            time.sleep(0.5)
    return wlan.ifconfig()

# --- Tasks ---
async def temp_task():
    while True:
        try:
            dht_sensor.measure()
            t = dht_sensor.temperature()
            h = dht_sensor.humidity()
            state["temp"] = t
            state["hum"] = h
            state["last_update"] = time.time()
        except Exception as e:
            # lectura fallida, mantenemos valor anterior
            state["temp"] = None
        await asyncio.sleep(0.5)

async def auto_cycle_task():
    """Ciclo automático del semáforo"""
    while True:
        if state["mode"] == "auto":
            set_light("red")
            await asyncio.sleep(DUR_RED)
            if state["mode"] != "auto": continue
            set_light("green")
            await asyncio.sleep(DUR_GREEN)
            if state["mode"] != "auto": continue
            set_light("yellow")
            await asyncio.sleep(DUR_YELLOW)
            # loop
        else:
            await asyncio.sleep(0.5)

# --- Simple HTTP server using uasyncio streams ---
HTML_PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Semáforo ESP32</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:Arial,Helvetica,sans-serif;background:#111;color:#eee;display:flex;flex-direction:column;align-items:center;padding:20px}
.container{display:flex;gap:40px;align-items:flex-start}
.traffic{width:140px;background:#222;padding:16px;border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,.6)}
.bulb{width:90px;height:90px;border-radius:50%;background:#333;margin:12px auto;transition:0.25s box-shadow,0.25s transform}
.bulb.off{filter:brightness(.25);box-shadow:none;transform:scale(.98)}
.bulb.red{background:linear-gradient(#a00,#600)}
.bulb.yellow{background:linear-gradient(#cc0,#885500)}
.bulb.green{background:linear-gradient(#0a0,#044)}
.controls{display:flex;flex-direction:column;gap:8px}
.btn{padding:8px 12px;border-radius:8px;border:none;background:#1a73e8;color:white;cursor:pointer}
.small{font-size:0.9rem;color:#bbb}
.panel{background:#161616;padding:14px;border-radius:10px;min-width:220px}
.row{display:flex;justify-content:space-between;align-items:center;margin:6px 0}
.switch{display:flex;gap:8px;align-items:center}
.mode-indicator{padding:6px 10px;border-radius:10px;background:#222}
</style>
</head>
<body>
<h2>Semáforo ESP32 — Simulación + Físico</h2>
<div class="container">
  <div class="traffic">
    <div id="red" class="bulb red off"></div>
    <div id="yellow" class="bulb yellow off"></div>
    <div id="green" class="bulb green off"></div>
  </div>

  <div style="display:flex;flex-direction:column;gap:12px">
    <div class="panel">
      <div class="row"><strong>Modo</strong><span id="mode" class="mode-indicator">--</span></div>
      <div style="display:flex;gap:6px;margin-top:8px">
        <button class="btn" onclick="setMode('auto')">Auto</button>
        <button class="btn" onclick="setMode('manual')">Manual</button>
      </div>
      <div style="margin-top:10px" class="small">En modo manual puedes elegir una luz:</div>
      <div style="display:flex;gap:8px;margin-top:8px">
        <button class="btn" onclick="manualLight('red')">Rojo</button>
        <button class="btn" onclick="manualLight('yellow')">Amarillo</button>
        <button class="btn" onclick="manualLight('green')">Verde</button>
      </div>
    </div>

    <div class="panel">
      <div style="font-weight:bold;margin-bottom:6px">Dashboard temperatura</div>
      <div class="row"><span>Temperatura</span><span id="temp">-- °C</span></div>
      <div class="row"><span>Humedad</span><span id="hum">-- %</span></div>
      <div class="row small"><span>Última</span><span id="last">--</span></div>
    </div>
  </div>
</div>

<script>
async function fetchStatus(){
  try{
    const resp = await fetch('/status');
    if(!resp.ok) throw 'err';
    const j = await resp.json();
    // update lights
    document.getElementById('red').classList.toggle('off', j.light !== 'red');
    document.getElementById('yellow').classList.toggle('off', j.light !== 'yellow');
    document.getElementById('green').classList.toggle('off', j.light !== 'green');
    document.getElementById('mode').innerText = j.mode;
    document.getElementById('temp').innerText = j.temp !== null ? j.temp.toFixed(1)+' °C' : '--';
    document.getElementById('hum').innerText = j.hum !== null ? j.hum.toFixed(1)+' %' : '--';
    document.getElementById('last').innerText = j.last ? new Date(j.last*1000).toLocaleTimeString() : '--';
  }catch(e){
    console.log('status error', e);
  }
}

async function setMode(mode){
  await fetch('/control', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({mode:mode})});
  fetchStatus();
}
async function manualLight(light){
  await fetch('/control', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({mode:'manual',light:light})});
  fetchStatus();
}

// poll every second
setInterval(fetchStatus, 1000);
fetchStatus();
</script>
</body>
</html>
"""

async def handle_client(reader, writer):
    try:
        req = await reader.readline()
        if not req:
            await writer.aclose(); return
        req_line = req.decode()
        parts = req_line.split()
        if len(parts) < 2:
            await writer.aclose(); return
        method = parts[0]
        path = parts[1]
        # read headers
        headers = {}
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break
            h = line.decode().split(":",1)
            if len(h)==2:
                headers[h[0].strip().lower()] = h[1].strip()
        body = None
        if method == "POST":
            cl = int(headers.get("content-length","0"))
            if cl:
                body = await reader.readexactly(cl)
        # Routing
        if path == "/" and method == "GET":
            content = HTML_PAGE
            writer.write(b"HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n")
            writer.write(content.encode('utf-8'))
            await writer.drain()
        elif path == "/status" and method == "GET":
            j = {
                "mode": state["mode"],
                "light": state["light"],
                "temp": state["temp"],
                "hum": state["hum"],
                "last": state["last_update"]
            }
            b = ujson.dumps(j)
            writer.write(b"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n")
            writer.write(b.encode('utf-8'))
            await writer.drain()
        elif path == "/control" and method == "POST":
            if body:
                try:
                    payload = ujson.loads(body)
                    mode = payload.get("mode")
                    if mode in ("auto","manual"):
                        state["mode"] = mode
                    light = payload.get("light")
                    if light in ("red","yellow","green"):
                        # if manual request, set light; if auto, will be ignored by cycle task until mode auto
                        set_light(light)
                    resp = {"ok": True, "mode": state["mode"], "light": state["light"]}
                except Exception as e:
                    resp = {"ok": False, "error": str(e)}
            else:
                resp = {"ok": False, "error": "no body"}
            b = ujson.dumps(resp)
            writer.write(b"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n")
            writer.write(b.encode('utf-8'))
            await writer.drain()
        else:
            writer.write(b"HTTP/1.0 404 Not Found\r\n\r\n")
            await writer.drain()
    except Exception as e:
        # best effort
        try:
            writer.write(b"HTTP/1.0 500 Internal Error\r\n\r\n")
            await writer.drain()
        except:
            pass
    finally:
        try:
            await writer.aclose()
        except:
            pass

async def start_server():
    srv = await asyncio.start_server(handle_client, "0.0.0.0", 80)
    await srv.wait_closed()

# --- Main ---
def run():
    print("Conectando WiFi...")
    try:
        ip = connect_wifi(SSID, PASSWORD)
        print("Conectado. IP:", ip[0])
    except Exception as e:
        print("WiFi error:", e)
        # continuar localmente, pero sin red no servirá
    loop = asyncio.get_event_loop()
    loop.create_task(temp_task())
    loop.create_task(auto_cycle_task())
    loop.create_task(start_server())
    print("Servidor HTTP iniciado en puerto 80")
    loop.run_forever()

# Ejecutar si se importa como main
if __name__ == "__main__":
    run()
