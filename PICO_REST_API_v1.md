# Pico REST API v1 – Technische Referenz

**Stand:** 01.09.2026  
**Umgebung:** Raspberry Pi Pico W / MicroPython  
**Herstellerkennung:** `HSZ-IT`

Diese Dokumentation beschreibt den gemeinsamen technischen Standard der aktuell
eingesetzten Pico-REST-Geräte sowie die Konventionen für zukünftige Geräte.

---

## 1. Ziel und Grundprinzip

Pico REST API v1 stellt eine möglichst einheitliche HTTP-Schnittstelle für
verschiedene Raspberry-Pi-Pico-W-Anwendungen bereit.

Die Geräte unterscheiden sich in ihrer eigentlichen Funktion, verwenden aber
gemeinsame Konventionen für:

- Geräteidentifikation
- Statusabfrage
- WLAN-Status
- Schreibschutz
- externe Zugangsdaten
- OTA-Firmwareupdate
- Neustart
- Home-Assistant-Integration

Die API ist bewusst einfach gehalten und für den Betrieb in einem geschützten
lokalen Netzwerk vorgesehen.

---

## 2. Aktueller Gerätebestand

| Gerät | `device_type` | IP | Firmware |
|---|---|---|---|
| Pool-Steuerung | `pool_controller` | `192.168.6.148` | `3.6.0` |
| LED-Steuerung | `led_controller` | `192.168.6.130` | `4.4.0` |
| Aufzugsmonitor | `elevator_monitor` | `192.168.6.123` | `1.5.0` |
| Sonnen-/Windmonitor | `sun_wind_monitor` | `192.168.6.140` | `2.4.0` |
| Pool-Sensorserver | `pool_sensor_monitor` | `192.168.6.164` | `1.5.0` |

Alle fünf Geräte verwenden inzwischen:

- Pico REST API v1
- stabile `device_id`
- Bearer-Authentifizierung für Schreibzugriffe
- externe `secrets.py`
- einheitlichen `system`-Block in `/api/status`

---

## 3. Basis-Endpunkte

Die kanonischen Endpunkte sind:

```text
GET  /api/info
GET  /api/status
GET  /api/config        sofern vom Gerät unterstützt

POST /api/config        sofern vom Gerät unterstützt
POST /api/ota
POST /api/reboot
```

Gerätespezifisch können weitere Endpunkte hinzukommen.

Legacy-Endpunkte ohne `/api/` dürfen aus Gründen der Rückwärtskompatibilität
weiterhin vorhanden sein. Für neue Software soll grundsätzlich die
`/api/...`-Variante verwendet werden.

---

## 4. `/api/info`

`GET /api/info` dient zur Erkennung und Beschreibung des Gerätes.

Minimaler gemeinsamer Aufbau:

```json
{
  "api": "pico-rest",
  "api_version": 1,
  "device_id": "eindeutige-hardware-id",
  "device_type": "pool_controller",
  "device_name": "Gerätename",
  "manufacturer": "HSZ-IT",
  "hardware": "Raspberry Pi Pico W",
  "firmware": "3.6.0",
  "auth": {
    "write": "bearer"
  },
  "security": {
    "secrets_external": true,
    "secrets_migration": false
  }
}
```

### `device_id`

Die `device_id` wird aus `machine.unique_id()` erzeugt und muss über
Firmwareupdates hinweg stabil bleiben.

Sie ist die primäre technische Geräteidentität. Eine Änderung von IP-Adresse
oder Anzeigename darf die `device_id` nicht verändern.

### `device_type`

Aktuell definierte Typen:

```text
pool_controller
led_controller
elevator_monitor
sun_wind_monitor
pool_sensor_monitor
```

Neue Geräte erhalten einen neuen, dauerhaft stabilen `device_type`.

### `api_version`

Aktuell:

```text
1
```

Additive Erweiterungen, beispielsweise zusätzliche JSON-Felder, erfordern
keine Erhöhung der API-Version, solange bestehende Clients kompatibel bleiben.

---

## 5. `/api/status`

`GET /api/status` liefert den aktuellen Gerätezustand.

Gerätespezifische Felder bleiben erlaubt. Zusätzlich enthält jedes Gerät den
gemeinsamen Block:

```json
{
  "system": {
    "time": [2026, 8, 29, 8, 30, 0, 5, 241],
    "cpu_temp": 40.2,
    "free_mem": 251504,
    "ip": "192.168.6.148",
    "firmware": "3.6.0",
    "wifi": {
      "connected": true,
      "rssi": -52,
      "quality": "vgood",
      "reconnects": 0,
      "interface_resets": 0,
      "offline_sec": 0
    }
  }
}
```

Vorhandene Legacy-Felder auf oberster JSON-Ebene dürfen parallel erhalten
bleiben.

---

## 6. WLAN-Qualität

Für alle Geräte gilt folgende gemeinsame Bewertung:

| RSSI | `quality` |
|---:|---|
| `>= -50 dBm` | `excellent` |
| `>= -60 dBm` | `vgood` |
| `>= -70 dBm` | `good` |
| `>= -80 dBm` | `fair` |
| `>= -90 dBm` | `weak` |
| `< -90 dBm` | `poor` |

Die Grenzwerte sind inklusiv.

Kann kein gültiger RSSI-Wert bestimmt werden, soll langfristig bevorzugt

```json
{
  "rssi": null,
  "quality": "unknown"
}
```

verwendet werden. Ein künstlich erfundener Messwert soll nicht als echter
RSSI ausgegeben werden.

---

## 7. Authentifizierung

### 7.1 Grundsatz

**Lesende Zugriffe bleiben ohne Authentifizierung möglich.**

Beispiele:

```text
GET /api/info
GET /api/status
GET /api/config
```

**Alle zustandsverändernden HTTP-Zugriffe benötigen Bearer-Authentifizierung.**

Dazu gehören insbesondere:

```text
POST /api/config
POST /api/ota
POST /api/reboot
POST /api/reset
POST /api/rollback
```

sowie gerätespezifische Steuerbefehle.

### 7.2 HTTP-Header

```http
Authorization: Bearer <API_TOKEN>
```

Beispiel mit `curl`:

```bash
TOKEN='...'

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://192.168.6.123/api/reboot
```

Der Token gehört **niemals**:

- in die URL
- in Query-Parameter
- in `/api/info`
- in `/api/status`
- in `/api/config`
- in Log-Ausgaben

### 7.3 Fehlende oder falsche Authentifizierung

Antwort:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="pico-rest"
```

JSON:

```json
{
  "error": "unauthorized",
  "auth": "bearer"
}
```

### 7.4 Sicherheitsgrenze

Die Pico-Geräte verwenden HTTP und kein HTTPS.

Der Bearer-Token schützt daher vor nicht autorisierten Schreibzugriffen,
verschlüsselt aber den Netzwerkverkehr nicht. Das Sicherheitsmodell setzt
zusätzlich ein vertrauenswürdiges bzw. entsprechend isoliertes WLAN/LAN voraus.

---

## 8. `secrets.py`

Zugangsdaten werden nicht mehr in `main.py` gespeichert.

Auf jedem Pico existiert lokal:

```python
WIFI_SSID = "..."
WIFI_PASSWORD = "..."
API_TOKEN = "..."
```

in der Datei:

```text
secrets.py
```

Die produktive Firmware importiert ausschließlich:

```python
try:
    from secrets import WIFI_SSID, WIFI_PASSWORD, API_TOKEN
except Exception:
    print("FEHLER: secrets.py fehlt oder ist ungueltig")
    raise RuntimeError("secrets.py required")
```

### Wichtige Regel

Es gibt **keine Default- oder Fallback-Secrets** in `main.py`.

Fehlt `secrets.py`, soll das Gerät nicht stillschweigend mit eingebetteten
Standardzugangsdaten starten.

`secrets.py` darf nicht in ein öffentliches Git-Repository eingecheckt werden.

Empfohlener `.gitignore`-Eintrag:

```gitignore
secrets.py
```

---

## 9. OTA-Firmwareupdate

Firmwareupdates erfolgen über:

```text
POST /api/ota
```

Beispiel:

```bash
TOKEN='...'

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  --data-binary @main.py \
  http://192.168.6.140/api/ota
```

Grundprinzip:

```text
neue Firmware
     |
     v
temporäre Datei
     |
     v
vorhandene main.py -> Backup
     |
     v
neue Datei -> main.py
     |
     v
Neustart
```

Die konkrete Backup-Bezeichnung kann historisch je nach Firmware variieren.
Neue Implementierungen sollen möglichst einheitlich vorgehen.

### Secrets und OTA

`secrets.py` wird durch ein normales OTA-Update von `main.py` **nicht**
überschrieben.

Damit bleiben WLAN-Zugang und API-Token über Firmwareupdates hinweg erhalten.

---

## 10. Historische Secrets-Migration

Die fünf bestehenden Geräte wurden zweistufig migriert:

```text
alte Firmware mit eingebetteten Secrets
             |
             v
Übergangsfirmware
             |
             v
POST /api/migrate-secrets
             |
             v
secrets.py wird lokal erzeugt
             |
             v
saubere Firmware ohne eingebettete Secrets
```

Der temporäre Migrationsendpunkt war ebenfalls Bearer-geschützt.

Nach erfolgreicher Migration wurde das letzte Backup der Übergangsfirmware
entfernt, weil dieses noch Klartext-Secrets enthielt.

### Aktueller Zustand

Die Migration ist abgeschlossen.

Produktive Firmware soll daher **keinen** `/api/migrate-secrets`-Endpunkt mehr
benötigen und in `/api/info` melden:

```json
{
  "security": {
    "secrets_external": true,
    "secrets_migration": false
  }
}
```

---

## 11. Home Assistant

Die Custom Integration **Pico REST v0.5.2** unterstützt die aktuelle
Schnittstelle.

Sie verwendet:

- `/api/info` zur Geräteerkennung
- `/api/status` zur Zustandsabfrage
- gerätespezifische REST-Funktionen zur Steuerung
- Bearer-Token ausschließlich für Schreibzugriffe

Der API-Token wird in Home Assistant konfiguriert und nicht an die
Frontend-JavaScript-Karten weitergereicht.

### Frontend

v0.5.2 verwendet hash-basiertes Cache-Busting für die ausgelieferten
JavaScript-Dateien.

Schema:

```text
/pico_rest_static/<build-hash>/<javascript-datei>
```

Damit ändert sich die URL automatisch, sobald sich eine ausgelieferte
Frontend-Datei ändert.

---

## 12. Gerätespezifische Funktionen

### Pool-Steuerung

`device_type`:

```text
pool_controller
```

Zusätzlich zur gemeinsamen API besitzt sie Funktionen für unter anderem:

- Pumpensteuerung
- Ventilsteuerung
- AUTO/CLEAN/MANUAL
- Temperaturregelung
- Konfiguration
- Sensor-/Anomalieinformationen

Aktuelle Firmware:

```text
3.6.0
```

### LED-Steuerung

`device_type`:

```text
led_controller
```

Gerätespezifisch:

- LED-Farben
- Effekte
- Wochenplan
- Effektgeschwindigkeit
- globale und tagesabhängige Konfiguration
- Aufzugsstatus/-effekte

Aktuelle Firmware:

```text
4.4.0
```

### Aufzugsmonitor

`device_type`:

```text
elevator_monitor
```

Gerätespezifisch:

- Fahrtrichtung
- Stillstand
- Plausibilitätsstatus der Eingänge

Aktuelle Firmware:

```text
1.5.0
```

### Sonnen-/Windmonitor

`device_type`:

```text
sun_wind_monitor
```

Gerätespezifisch:

- Wind
- Böenerkennung
- Helligkeit
- Relaisausgänge

Aktuelle Firmware:

```text
2.4.0
```

### Pool-Sensorserver

`device_type`:

```text
pool_sensor_monitor
```

Gerätespezifisch:

- mehrere I²C-Sensoren
- Distanz
- Signalstärke
- Sensortemperatur
- Sensoranzahl

Aktuelle Firmware:

```text
1.5.0
```

---

## 13. Vorgaben für neue Pico-REST-Geräte

Für neue Geräte sollte folgende Checkliste gelten:

1. `GET /api/info` implementieren.
2. Stabile `device_id` aus `machine.unique_id()` verwenden.
3. Eindeutigen und dauerhaften `device_type` vergeben.
4. `api_version: 1` verwenden, solange die API kompatibel bleibt.
5. `manufacturer: "HSZ-IT"` setzen.
6. `firmware` in `/api/info` und `/api/status` ausgeben.
7. Gemeinsamen `system`-Block in `/api/status` implementieren.
8. Einheitliche WLAN-Qualitätsstufen verwenden.
9. Lesezugriffe ohne Authentifizierung ermöglichen.
10. Sämtliche Schreibzugriffe mit Bearer-Token schützen.
11. Token ausschließlich aus `secrets.py` laden.
12. WLAN-SSID und Passwort ausschließlich aus `secrets.py` laden.
13. Keine Secrets in REST-Antworten oder Logs ausgeben.
14. OTA über `/api/ota` unterstützen.
15. `secrets.py` bei OTA nicht verändern.
16. Vorhandene Sicherheits-/Hardware-Interlocks niemals durch REST umgehen.
17. Bestehende Legacy-Endpunkte nur zur Kompatibilität erhalten; neue Clients
    verwenden `/api/...`.

---

## 14. Empfohlenes Grundgerüst für `/api/info`

```python
def get_info():
    return {
        "api": "pico-rest",
        "api_version": 1,
        "device_id": get_device_id(),
        "device_type": DEVICE_TYPE,
        "device_name": DEVICE_NAME,
        "manufacturer": "HSZ-IT",
        "hardware": "Raspberry Pi Pico W",
        "firmware": VERSION,
        "auth": {
            "write": "bearer",
        },
        "security": {
            "secrets_external": True,
            "secrets_migration": False,
        },
        "capabilities": [
            "status",
            "reboot",
            "ota",
        ],
    }
```

---

## 15. Empfohlenes Grundgerüst für externe Secrets

```python
try:
    from secrets import WIFI_SSID, WIFI_PASSWORD, API_TOKEN
except Exception:
    print("FEHLER: secrets.py fehlt oder ist ungueltig")
    raise RuntimeError("secrets.py required")
```

Keine Secret-Werte in Fehlermeldungen ausgeben.

---

## 16. Kompatibilitätsprinzip

Der Pico-REST-Standard wird möglichst **additiv** weiterentwickelt.

Das bedeutet:

- bestehende JSON-Felder nicht ohne Not entfernen
- neue Felder ergänzen statt alte umzubenennen
- Legacy-Felder zunächst weiterführen
- Home Assistant muss ältere Geräteversionen weiterhin erkennen können
- inkompatible Änderungen erfordern eine bewusste neue API-Version

Damit können Firmware und Home-Assistant-Integration unabhängig voneinander
aktualisiert werden, ohne alle Pico-Geräte gleichzeitig aktualisieren zu
müssen.

---

## 17. Versionsstand dieser Referenz

```text
Pico REST API:             v1
Home-Assistant-Integration: v0.5.2

Pool-Steuerung:             v3.6.0
LED-Steuerung:              v4.4.0
Aufzugsmonitor:             v1.5.0
Sonnen-/Windmonitor:        v2.4.0
Pool-Sensorserver:          v1.5.0
```

**Status:** Bearer-Authentifizierung und Migration auf externe `secrets.py`
sind bei allen fünf Geräten abgeschlossen.
