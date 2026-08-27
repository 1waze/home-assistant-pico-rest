# Changelog

## 0.4.2

- Add a dedicated Home Assistant RGB color-wheel panel for Pico REST LED controllers.
- Provide unrestricted RGB selection for every weekday schedule and for `color1` / `color2`.
- Write colors directly through Pico REST `/api/config`; no LED firmware update is required.
- Remove the experimental light entities used by the first v0.4.2 test build.
- Automatically clean up those obsolete test entities from the entity registry.

## 0.4.1

- UX cleanup for the automatic Home Assistant device pages.
- Shorten and standardize writable entity names.
- Rename pool differential controls to `Differenz Einschalten` and `Differenz Ausschalten`.
- Rename sun/wind threshold controls to clearer German labels.
- Disable redundant read-only pool mode/cleaning entities by default.
- Disable duplicate LED config and weekly schedule sensors by default; writable controls remain visible.
- Disable API version, firmware, IP address and last-successful-contact entities by default.
- Migrate existing v0.4.0 registry entries to the new disabled defaults without deleting them.
- Prevent the last-successful-contact timestamp from flooding the Home Assistant activity log by disabling that diagnostic entity by default.

## 0.4.0

- Add manual pool pump and valve switches; they are only available in manual mode.
- Add a capability-driven firmware rollback button, disabled by default.
- Keep reboot capability-driven and surface Pico action errors as Home Assistant errors.
- Reject Pico REST action responses that explicitly return `ok: false`.
- Create writable config entities only when the Pico advertises the `config` capability.
- Add LED controls for effect delay, elevator delay, and elevator polling interval.
- Refresh coordinator data immediately after successful config writes.

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
