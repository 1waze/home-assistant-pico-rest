# Home Assistant Pico REST

Custom Integration für Geräte mit **Pico REST API v1**.

## Unterstützte Gerätetypen

- `pool_controller`
- `led_controller`
- `elevator_monitor`
- `sun_wind_monitor`
- `pool_sensor_monitor`

## Aktueller Stand

**Release:** v0.4.3  
**Entwicklung:** v0.4.4

v0.4.4 erweitert die globale Pico-LED-Konfigurationskarte um alle nicht wochentagsbezogenen Einstellungen. Die Wochentagskarten aus v0.4.3 bleiben unverändert.

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
- Montag bis Sonntag: Ein-/Ausschaltzeit und Effekt als Entities
- Eigenes Panel **Pico REST Farben** mit freiem RGB-Farbrad für alle Wochentagsfarben
- Freie RGB-Farbräder für `Farbe 1` und `Farbe 2` des `two_color`-Effekts
- Globale LED-Konfigurationskarte für allgemeine Effekte, Helligkeit, Standort, Sonnenuntergang, Aufzug und Hardware-/Legacy-Einstellungen
- Breitengrad und Längengrad zusätzlich als schreibbare Number-Entities

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


## Lovelace-Karten

Die Integration liefert die Wochentagskarte `custom:pico-rest-day-card` und ab
v0.4.4 die vollständige globale LED-Konfigurationskarte
`custom:pico-rest-led-config-card` automatisch mit.

Beispiel Wochentag:

```yaml
type: custom:pico-rest-day-card
day: 1
title: Dienstag
```

Globale LED-Konfiguration:

```yaml
type: custom:pico-rest-led-config-card
title: Globale LED-Konfiguration
```

Die globale Karte enthält alle nicht wochentagsbezogenen Werte aus `/api/config`:
allgemeine LED-/Effektparameter, `color1`/`color2`, Standort und Sonnenuntergang,
Aufzugparameter sowie erweiterte Hardware-/Legacy-Werte. Die Karte aktualisiert sich
automatisch bei externen Konfigurationsänderungen.

Im final getesteten Sections-Layout belegen die Wochentagskarten 9 Grid-Spalten und
die globale LED-Konfigurationskarte 18 Grid-Spalten.

`day` verwendet `0` = Montag bis `6` = Sonntag. Bei mehreren LED-Controllern kann
bei beiden Kartentypen zusätzlich `device_name` oder `entry_id` angegeben werden.
