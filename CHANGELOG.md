# Changelog

## 0.3.0

- Use Pico hardware `device_id` as stable Home Assistant config-entry, device, and entity identity.
- Migrate v0.2.x host-based device/entity unique IDs in place to preserve existing entity IDs and customizations.
- Add reconfigure flow for changing IP address/hostname without deleting the integration.
- Verify the hardware identity during reconfiguration.
- Mark coordinator-backed entities unavailable when polling fails and recover automatically.
- Improve setup error handling for unreachable and invalid Pico REST devices.
- Revalidate `/api/info` periodically and reject identity changes at the configured host.
- Add diagnostic sensor for the last successful contact.
- Require Pico REST API v1 `device_id`.

## 0.2.1

- Fix Home Assistant/HACS manifest validation by adding codeowners, documentation and issue tracker.
- Add local brand icon required by HACS.
- Fix Ruff style issues in sensor and binary sensor platforms.
- Use the Python 3.13 `type` alias syntax for the config entry alias.

## 0.2.0

- Erste schreibende Version der Integration.
- Poolsteuerung: Betriebsmodus, Reinigungsmodus, Solltemperatur, Ein-/Ausschaltdifferenz und Pumpenzeiten steuerbar.
- LED-Steuerung: Helligkeit, Effektparameter, Sonnenuntergangsnutzung, Aufzug-Effekt/-Geschwindigkeit sowie Wochenzeiten und Wochentagseffekte steuerbar.
- Sonnen-/Windabfrage: Grenzwerte `max_wind`, `max_boe` und `max_hell` steuerbar.
- Reboot-Button für alle Geräte mit `reboot`-Capability.
- `free_mem` wird wieder als echter ganzzahliger Byte-Wert an Home Assistant geliefert; Anzeigepräzision 0.
- Lesende Entities aus v0.1.1 bleiben erhalten.

## 0.1.1

- LED-Wochenplan aus `/api/config` als read-only Sensoren ergänzt.
- `/api/config` wird für Geräte mit `config`-Capability zentral mitgepollt.
- Erste Verbesserung der Speicheranzeige.

## 0.1.0

- Erste lesende Integration.
- Config Flow und automatische Erkennung über `/api/info`.
- Status-Polling über `DataUpdateCoordinator`.
- Sensoren/Binary-Sensoren für fünf Pico-REST-v1-Gerätetypen.
