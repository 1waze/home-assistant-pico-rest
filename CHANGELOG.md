# Changelog

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
