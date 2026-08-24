# Contributing

Thanks for helping improve Pico REST for Home Assistant.

## Development workflow

1. Create a feature branch from `main`.
2. Keep changes focused and backwards-compatible where practical.
3. Update `CHANGELOG.md` for user-visible changes.
4. Run the local checks before committing:

```bash
python -m compileall -q custom_components tests
ruff check custom_components tests
```

5. Open a pull request against `main`.

## Pico REST API

Changes that affect the device protocol must also update
`docs/pico-rest-api-v1.md`.

The integration should keep legacy Pico endpoints working where the firmware
already exposes them, but new Home Assistant code should use `/api/*`.
