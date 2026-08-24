# Installation / Update

## Update von v0.1.x auf v0.2.0

1. Home Assistant nicht zwingend vorher stoppen.
2. Den vorhandenen Ordner `/config/custom_components/pico_rest` durch den Ordner `custom_components/pico_rest` aus diesem Paket ersetzen.
3. Home Assistant neu starten.
4. Die bereits eingerichteten Pico-Geräte müssen nicht neu hinzugefügt werden.

Nach dem Neustart erscheinen bei Geräten mit `config`-Capability zusätzliche `number`, `select`, `switch` und `time` Entities. Bei Geräten mit `reboot`-Capability erscheint ein Neustart-Button.

Hinweis: Die alten read-only Sensoren bleiben bestehen; damit bleiben vorhandene Dashboards und Automationen kompatibel.
