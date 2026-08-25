# Home Assistant Pico REST

Custom Integration für Geräte mit **Pico REST API v1**.

## Unterstützte Gerätetypen

- `pool_controller`
- `led_controller`
- `elevator_monitor`
- `sun_wind_monitor`
- `pool_sensor_monitor`

## Version 0.2.1

v0.2.1 enthält die v0.2.0-Steuerfunktionen und korrigiert die GitHub/HACS/Hassfest-Validierung.

### Poolsteuerung

- Betriebsmodus (`auto` / `manual`)
- Reinigungsmodus
- Solltemperatur
- Temperaturdifferenz Ein/Aus
- Pumpen-Ein-/Ausschaltzeit

### LED-Steuerung

- Sonnenuntergang verwenden
- Helligkeit
- Effektgeschwindigkeit
- Effektintensität
- Zweifarben-Aufteilung
- Standard-Effekt
- Aufzug-Effekt und Aufzug-Geschwindigkeit
- Montag bis Sonntag: Ein-/Ausschaltzeit und Effekt

Die vorhandenen read-only Wochenplan-Sensoren aus v0.1.1 bleiben aus Kompatibilitätsgründen erhalten.

### Sonnen-/Windabfrage

- Wind-Grenzwert
- Böen-Zähler-Grenzwert
- Helligkeits-Grenzwert

### Wartung

Geräte mit `reboot`-Capability erhalten einen Neustart-Button.

OTA, Rollback und Factory-Reset sind in v0.2.0 absichtlich noch nicht als HA-Aktionen freigegeben.

## Installation

Den Ordner

`custom_components/pico_rest`

nach

`/config/custom_components/pico_rest`

kopieren und Home Assistant neu starten.

Danach unter **Einstellungen → Geräte & Dienste → Integration hinzufügen → Pico REST** den Host oder die IP-Adresse des Pico eintragen.

## Geräte-ID

Ab v0.3.0 verwendet die Integration die stabile `device_id` aus Pico REST API v1. Sie wird auf dem Pico aus `machine.unique_id()` abgeleitet und bleibt bei einem Wechsel der IP-Adresse oder des Hostnamens unverändert. Bestehende v0.2.x-Installationen werden beim ersten Start automatisch von der bisherigen Host-basierten Kennung migriert.

## Entwicklung

Die Integration ist als eigenständiges GitHub-/HACS-Repository aufgebaut.
Validierung erfolgt automatisch per GitHub Actions mit Hassfest, HACS und Ruff.

Lokale Prüfungen:

```bash
python -m compileall -q custom_components tests
ruff check custom_components tests
```

## Releases

Versionen folgen Semantic Versioning. Für veröffentlichte Stände wird ein
Git-Tag im Format `vX.Y.Z` verwendet, z. B. `v0.2.0`.

Siehe auch [CHANGELOG.md](CHANGELOG.md) und
[docs/pico-rest-api-v1.md](docs/pico-rest-api-v1.md).

## v0.3.0 device identity and availability

Version 0.3.0 uses the Pico REST API v1 `device_id` as stable hardware identity. Existing v0.2.x installations are migrated in place, including entity unique IDs, so existing Home Assistant entity IDs and customizations are retained.

The integration now supports Home Assistant's **Reconfigure** flow to change a Pico's IP address or hostname while verifying that the new address belongs to the same physical Pico. Coordinator-backed entities automatically become unavailable during communication failures and recover when the device returns.
