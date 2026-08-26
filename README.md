# Home Assistant Pico REST

Custom Integration für Geräte mit **Pico REST API v1**.

## Unterstützte Gerätetypen

- `pool_controller`
- `led_controller`
- `elevator_monitor`
- `sun_wind_monitor`
- `pool_sensor_monitor`

## Aktueller Stand

**Release:** v0.4.0

v0.4.0 erweitert die bereits vorhandenen Steuerfunktionen um zusätzliche native Home-Assistant-Bedienelemente.

### Poolsteuerung

- Betriebsmodus (`auto` / `manual`)
- Reinigungsmodus
- Solltemperatur
- Temperaturdifferenz Ein/Aus
- Pumpen-Ein-/Ausschaltzeit
- Pumpe manuell schalten (nur im manuellen Modus verfügbar)
- Ventil manuell schalten (nur im manuellen Modus verfügbar)

### LED-Steuerung

- Sonnenuntergang verwenden
- Helligkeit
- Effektgeschwindigkeit und Effektintensität
- Effekt-Verzögerung
- Zweifarben-Aufteilung
- Standard-Effekt
- Aufzug-Effekt und Aufzug-Geschwindigkeit
- Aufzug-Verzögerung und Aufzug-Abfrageintervall
- Montag bis Sonntag: Ein-/Ausschaltzeit und Effekt

Die vorhandenen read-only Wochenplan-Sensoren bleiben aus
Kompatibilitätsgründen erhalten.

### Sonnen-/Windabfrage

- Wind-Grenzwert
- Böen-Zähler-Grenzwert
- Helligkeits-Grenzwert

### Wartung

Wartungsaktionen werden anhand der von `/api/info` gemeldeten
`capabilities` erzeugt:

- Neustart
- Firmware-Rollback (standardmäßig deaktiviert)

OTA selbst wird weiterhin nicht direkt aus Home Assistant ausgelöst.

## Geräte-ID und Verfügbarkeit

Seit v0.3.0 verwendet die Integration die stabile `device_id` aus Pico REST
API v1. Bestehende v0.2.x-Installationen werden automatisch migriert.
Ein Reconfigure-Flow erlaubt Änderungen von IP-Adresse oder Hostname, ohne
das Gerät in Home Assistant neu anzulegen.

## Installation

Empfohlen ist die Installation über HACS als Custom Repository. Alternativ
kann `custom_components/pico_rest` nach `/config/custom_components/pico_rest`
kopiert werden. Danach Home Assistant neu starten und unter
**Einstellungen → Geräte & Dienste → Integration hinzufügen → Pico REST**
den Pico hinzufügen.

## Entwicklung

Die Integration ist als eigenständiges GitHub-/HACS-Repository aufgebaut.
Validierung erfolgt per GitHub Actions mit Hassfest, HACS und Ruff.

Lokale Prüfungen:

```bash
python -m compileall -q custom_components tests
ruff check custom_components tests
```

Versionen folgen Semantic Versioning. Für veröffentlichte Stände wird ein
Git-Tag im Format `vX.Y.Z` verwendet.

Siehe auch [CHANGELOG.md](CHANGELOG.md) und
[docs/pico-rest-api-v1.md](docs/pico-rest-api-v1.md).
