const PICO_DAYS = [
  "Montag",
  "Dienstag",
  "Mittwoch",
  "Donnerstag",
  "Freitag",
  "Samstag",
  "Sonntag",
];

const PICO_EFFECTS = [
  "solid",
  "two_color",
  "rainbow",
  "pulse",
  "theater",
  "scanner",
  "sparkle",
  "matrix",
  "chevrons",
];

function prRgbToHex(rgb) {
  return `#${rgb.map((v) => Number(v).toString(16).padStart(2, "0")).join("")}`;
}

function prHsvToRgb(h, s, v) {
  const c = v * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = v - c;
  let r = 0;
  let g = 0;
  let b = 0;

  if (h < 60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];

  return [r, g, b].map((n) => Math.round((n + m) * 255));
}

function prRgbToHsv([r, g, b]) {
  r /= 255;
  g /= 255;
  b /= 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const d = max - min;
  let h = 0;

  if (d) {
    if (max === r) h = 60 * (((g - b) / d) % 6);
    else if (max === g) h = 60 * ((b - r) / d + 2);
    else h = 60 * ((r - g) / d + 4);
  }
  if (h < 0) h += 360;

  return [h, max === 0 ? 0 : d / max, max];
}

class PicoRestDayWheel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.rgb = [255, 255, 255];
    this.hsv = [0, 0, 1];
  }

  connectedCallback() {
    this.render();
  }

  set value(rgb) {
    this.rgb = [...(rgb || [255, 255, 255])];
    this.hsv = prRgbToHsv(this.rgb);
    if (this.isConnected) this.render();
  }

  get value() {
    return this.rgb;
  }

  emit() {
    this.dispatchEvent(
      new CustomEvent("color-change", {
        detail: [...this.rgb],
        bubbles: true,
        composed: true,
      }),
    );
  }

  render() {
    const [h, s, v] = this.hsv;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        canvas {
          width: var(--pico-wheel-size, 132px);
          height: var(--pico-wheel-size, 132px);
          display: block;
          margin: 0 auto;
          touch-action: none;
          cursor: crosshair;
        }
        .row {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-top: 5px;
          font-size: 11px;
        }
        .row input { flex: 1; min-width: 0; }
        .swatch {
          width: 22px;
          height: 22px;
          flex: 0 0 22px;
          border-radius: 50%;
          border: 1px solid var(--divider-color);
          background: ${prRgbToHex(this.rgb)};
        }
        .value {
          text-align: center;
          margin-top: 3px;
          font-size: 10px;
          color: var(--secondary-text-color);
          white-space: nowrap;
        }
        :host([compact]) { --pico-wheel-size: 92px; }
        :host([compact]) .row { margin-top: 3px; gap: 3px; font-size: 9px; }
        :host([compact]) .row > span:first-child { display: none; }
        :host([compact]) .swatch { width: 18px; height: 18px; flex-basis: 18px; }
        :host([compact]) .value { font-size: 8px; }
      </style>
      <canvas width="220" height="220"></canvas>
      <div class="row">
        <span>Hell.</span>
        <input type="range" min="0" max="100" value="${Math.round(v * 100)}">
        <span class="swatch"></span>
      </div>
      <div class="value">RGB ${this.rgb.join(", ")} · ${prRgbToHex(this.rgb).toUpperCase()}</div>
    `;

    const canvas = this.shadowRoot.querySelector("canvas");
    this.draw(canvas, h, s);

    const pick = (event) => {
      const rect = canvas.getBoundingClientRect();
      const scale = canvas.width / rect.width;
      const x = (event.clientX - rect.left) * scale - canvas.width / 2;
      const y = (event.clientY - rect.top) * scale - canvas.height / 2;
      const radius = canvas.width / 2 - 8;
      const distance = Math.min(radius, Math.hypot(x, y));
      let hue = (Math.atan2(y, x) * 180) / Math.PI + 90;
      if (hue < 0) hue += 360;

      this.hsv = [hue, distance / radius, this.hsv[2]];
      this.rgb = prHsvToRgb(...this.hsv);
      this.render();
      this.emit();
    };

    canvas.addEventListener("pointerdown", (event) => {
      canvas.setPointerCapture(event.pointerId);
      pick(event);
    });
    canvas.addEventListener("pointermove", (event) => {
      if (canvas.hasPointerCapture(event.pointerId)) pick(event);
    });

    this.shadowRoot.querySelector("input").addEventListener("input", (event) => {
      this.hsv[2] = Number(event.target.value) / 100;
      this.rgb = prHsvToRgb(...this.hsv);
      this.render();
      this.emit();
    });
  }

  draw(canvas, h, s) {
    const ctx = canvas.getContext("2d");
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const radius = cx - 8;
    const image = ctx.createImageData(canvas.width, canvas.height);

    for (let y = 0; y < canvas.height; y += 1) {
      for (let x = 0; x < canvas.width; x += 1) {
        const dx = x - cx;
        const dy = y - cy;
        const distance = Math.hypot(dx, dy);
        const index = (y * canvas.width + x) * 4;
        if (distance <= radius) {
          let hue = (Math.atan2(dy, dx) * 180) / Math.PI + 90;
          if (hue < 0) hue += 360;
          const rgb = prHsvToRgb(hue, distance / radius, 1);
          image.data[index] = rgb[0];
          image.data[index + 1] = rgb[1];
          image.data[index + 2] = rgb[2];
          image.data[index + 3] = 255;
        }
      }
    }
    ctx.putImageData(image, 0, 0);

    const angle = ((h - 90) * Math.PI) / 180;
    const markerRadius = s * radius;
    const px = cx + Math.cos(angle) * markerRadius;
    const py = cy + Math.sin(angle) * markerRadius;

    ctx.beginPath();
    ctx.arc(px, py, 7, 0, Math.PI * 2);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "white";
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(px, py, 9, 0, Math.PI * 2);
    ctx.lineWidth = 1;
    ctx.strokeStyle = "black";
    ctx.stroke();
  }
}

if (!customElements.get("pico-rest-day-wheel")) {
  customElements.define("pico-rest-day-wheel", PicoRestDayWheel);
}

class PicoRestDayCard extends HTMLElement {
  connectedCallback() {
    this.startRefreshTimer();
  }

  disconnectedCallback() {
    this.stopRefreshTimer();
  }

  startRefreshTimer() {
    if (this._refreshTimer) return;
    this._refreshTimer = setInterval(() => this.refreshFromBackend(), 5000);
  }

  stopRefreshTimer() {
    if (!this._refreshTimer) return;
    clearInterval(this._refreshTimer);
    this._refreshTimer = undefined;
  }

  setConfig(config) {
    if (config.day === undefined) {
      throw new Error("day ist erforderlich (0=Montag … 6=Sonntag)");
    }
    const day = Number(config.day);
    if (!Number.isInteger(day) || day < 0 || day > 6) {
      throw new Error("day muss zwischen 0 und 6 liegen");
    }
    this.config = { ...config, day };
    this._loaded = false;
    if (this._hass) this.load();
  }

  set hass(hass) {
    this._hass = hass;
    this.startRefreshTimer();
    if (this.config && !this._loaded) this.load();
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return {
      columns: 9,
      min_columns: 9,
    };
  }

  selectDevice(devices) {
    if (this.config.entry_id) {
      return devices.find((item) => item.entry_id === this.config.entry_id);
    }
    if (this.config.device_name) {
      return devices.find((item) => item.name === this.config.device_name);
    }
    if (devices.length === 1) return devices[0];
    if (devices.length > 1) {
      throw new Error(
        "Mehrere LED-Controller gefunden: entry_id oder device_name in der Karte angeben.",
      );
    }
    return undefined;
  }

  applyDeviceData(device, forceRender = true) {
    const nextDay = { ...(device.days?.[String(this.config.day)] || {}) };
    const nextColors = { ...(device.colors || {}) };
    const changed =
      !this._device ||
      this._device.available !== device.available ||
      JSON.stringify(this._day || {}) !== JSON.stringify(nextDay) ||
      JSON.stringify(this._colors || {}) !== JSON.stringify(nextColors);

    this._device = device;
    this._colors = nextColors;
    this._day = nextDay;
    this._draft = {
      ...nextDay,
      color: [...(nextDay.color || [255, 255, 255])],
    };

    if (forceRender && changed) this.render();
  }

  async refreshFromBackend() {
    if (!this._hass || !this.config || this._refreshing || this._saving) return;
    this._refreshing = true;
    try {
      const devices = await this._hass.callWS({ type: "pico_rest/led_colors" });
      const device = this.selectDevice(devices);
      if (!device) return;
      this.applyDeviceData(device, true);
    } catch (_error) {
      // A temporary refresh error must not replace a working card with an error view.
    } finally {
      this._refreshing = false;
    }
  }

  async load() {
    if (!this._hass || !this.config) return;
    this._loaded = true;
    this._error = null;

    try {
      const devices = await this._hass.callWS({ type: "pico_rest/led_colors" });
      const device = this.selectDevice(devices);
      if (!device) throw new Error("Keine passende Pico REST LED-Steuerung gefunden.");
      this.applyDeviceData(device, false);
    } catch (error) {
      this._error = String(error);
    }

    this.render();
  }

  render() {
    if (!this.config) return;
    const title = this.config.title || PICO_DAYS[this.config.day];

    if (this._error) {
      this.innerHTML = `<ha-card><div style="padding:12px"><b>${title}</b><p>${this._error}</p></div></ha-card>`;
      return;
    }

    if (!this._draft) {
      this.innerHTML = `<ha-card><div style="padding:12px">${title}: Lade…</div></ha-card>`;
      return;
    }

    const day = this._draft;
    const offline = !this._device.available;
    const twoColor = day.effect === "two_color";

    this.innerHTML = `
      <ha-card>
        <style>
          .wrap {
            padding: 12px;
            ${offline ? "opacity:.55" : ""}
          }
          h2 {
            font-size: 17px;
            line-height: 1.2;
            margin: 0 0 8px;
          }
          .offline {
            font-size: 11px;
            color: var(--secondary-text-color);
            margin: -3px 0 6px;
          }
          .content {
            display: grid;
            grid-template-columns: 116px minmax(76px, 1fr);
            gap: 7px;
            align-items: start;
          }
          .content.two-color {
            grid-template-columns: 1fr;
          }
          .wheel,
          .controls,
          .field { min-width: 0; }
          .wheel pico-rest-day-wheel {
            --pico-wheel-size: 108px;
          }
          .two-color-note {
            padding: 7px 9px;
            border-radius: 7px;
            background: var(--secondary-background-color);
            color: var(--secondary-text-color);
            font-size: 10px;
            line-height: 1.3;
          }
          .controls {
            display: flex;
            flex-direction: column;
            gap: 6px;
          }
          .times {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 5px;
          }
          .field {
            display: flex;
            flex-direction: column;
            gap: 3px;
            font-size: 11px;
            color: var(--secondary-text-color);
          }
          .field span { white-space: nowrap; }
          select,
          input[type="time"] {
            box-sizing: border-box;
            width: 100%;
            min-height: 34px;
            border: 1px solid var(--divider-color);
            border-radius: 7px;
            padding: 6px 7px;
            background: var(--card-background-color);
            color: var(--primary-text-color);
            font: inherit;
            font-size: 13px;
          }
          .status {
            min-height: 14px;
            font-size: 11px;
            color: var(--secondary-text-color);
          }
          @media (max-width: 260px) {
            .content { grid-template-columns: 1fr; }
            .wheel {
              width: 100%;
              max-width: 130px;
              margin: 0 auto;
            }
          }
        </style>
        <div class="wrap">
          <h2>${title}</h2>
          ${offline ? '<div class="offline">Nicht verfügbar</div>' : ""}
          <div class="content ${twoColor ? "two-color" : ""}">
            ${twoColor ? "" : `
              <div class="wheel">
                <pico-rest-day-wheel data-target="day"></pico-rest-day-wheel>
              </div>
            `}
            <div class="controls">
              ${twoColor ? '<div class="two-color-note">two_color nutzt die globalen Farben 1 + 2</div>' : ""}
              <label class="field">
                <span>Effekt</span>
                <select class="effect" ${offline ? "disabled" : ""}>
                  ${PICO_EFFECTS.map(
                    (effect) =>
                      `<option value="${effect}" ${effect === day.effect ? "selected" : ""}>${effect}</option>`,
                  ).join("")}
                </select>
              </label>
              <div class="times">
                <label class="field">
                  <span>Ein</span>
                  <input class="on" type="time" value="${day.on || ""}" ${offline ? "disabled" : ""}>
                </label>
                <label class="field">
                  <span>Aus</span>
                  <input class="off" type="time" value="${day.off || ""}" ${offline ? "disabled" : ""}>
                </label>
              </div>
              <div class="status"></div>
            </div>
          </div>
        </div>
      </ha-card>
    `;

    const wheel = this.querySelector('pico-rest-day-wheel[data-target="day"]');
    if (wheel) {
      wheel.value = day.color;
      wheel.addEventListener("color-change", (event) => {
        this.save({ color: event.detail }, true);
      });
    }
    this.querySelector(".effect").onchange = async (event) => {
      await this.save({ effect: event.target.value });
      this.render();
    };
    this.querySelector(".on").onchange = (event) => {
      this.save({ on: event.target.value });
    };
    this.querySelector(".off").onchange = (event) => {
      this.save({ off: event.target.value });
    };
  }

  async save(patch, debounce = false) {
    Object.assign(this._draft, patch);
    if (debounce) {
      clearTimeout(this._colorTimer);
      this._colorTimer = setTimeout(() => this.saveNow(patch), 350);
      return;
    }
    await this.saveNow(patch);
  }

  async saveNow(patch) {
    if (!this._device?.available) return;
    const status = this.querySelector(".status");
    if (status) status.textContent = "Speichere…";
    this._saving = true;

    try {
      await this._hass.callWS({
        type: "pico_rest/set_led_day",
        entry_id: this._device.entry_id,
        day: String(this.config.day),
        ...patch,
      });
      Object.assign(this._day, patch);
      if (status) status.textContent = "Gespeichert";
    } catch (error) {
      if (status) status.textContent = `Fehler: ${error}`;
    } finally {
      this._saving = false;
    }
  }
}

if (!customElements.get("pico-rest-day-card")) {
  customElements.define("pico-rest-day-card", PicoRestDayCard);
}


class PicoRestLedConfigCard extends HTMLElement {
  connectedCallback() { this.startRefreshTimer(); }
  disconnectedCallback() { this.stopRefreshTimer(); }

  setConfig(config) {
    this.config = { ...config };
    this._loaded = false;
    if (this._hass) this.load();
  }

  set hass(hass) {
    this._hass = hass;
    this.startRefreshTimer();
    if (this.config && !this._loaded) this.load();
  }

  getCardSize() { return 8; }

  getGridOptions() {
    return { columns: 18, min_columns: 12 };
  }

  startRefreshTimer() {
    if (this._refreshTimer) return;
    this._refreshTimer = setInterval(() => this.refreshFromBackend(), 5000);
  }

  stopRefreshTimer() {
    if (!this._refreshTimer) return;
    clearInterval(this._refreshTimer);
    this._refreshTimer = undefined;
  }

  selectDevice(devices) {
    if (this.config?.entry_id) return devices.find((item) => item.entry_id === this.config.entry_id);
    if (this.config?.device_name) return devices.find((item) => item.name === this.config.device_name);
    if (devices.length === 1) return devices[0];
    if (devices.length > 1) throw new Error("Mehrere LED-Controller gefunden: entry_id oder device_name angeben.");
    return undefined;
  }

  applyDeviceData(device, forceRender = true) {
    const nextConfig = { ...(device.config || {}) };
    const nextColors = { ...(device.colors || {}) };
    const changed = !this._device || this._device.available !== device.available ||
      this._elevatorState !== device.elevator_state ||
      JSON.stringify(this._global || {}) !== JSON.stringify(nextConfig) ||
      JSON.stringify(this._colors || {}) !== JSON.stringify(nextColors);
    this._device = device;
    this._elevatorState = device.elevator_state;
    this._global = nextConfig;
    this._colors = nextColors;
    if (forceRender && changed) this.render();
  }

  async refreshFromBackend() {
    if (!this._hass || !this.config || this._refreshing || this._saving) return;
    this._refreshing = true;
    try {
      const devices = await this._hass.callWS({ type: "pico_rest/led_colors" });
      const device = this.selectDevice(devices);
      if (device) this.applyDeviceData(device, true);
    } catch (_error) {
      // Keep last valid state.
    } finally { this._refreshing = false; }
  }

  async load() {
    if (!this._hass || !this.config) return;
    this._loaded = true;
    this._error = null;
    try {
      const devices = await this._hass.callWS({ type: "pico_rest/led_colors" });
      const device = this.selectDevice(devices);
      if (!device) throw new Error("Keine passende Pico REST LED-Steuerung gefunden.");
      this.applyDeviceData(device, false);
    } catch (error) { this._error = String(error); }
    this.render();
  }

  val(key, fallback = "") {
    const value = this._global?.[key];
    return value === undefined || value === null ? fallback : value;
  }

  elevatorStatusHtml() {
    const raw = String(this._elevatorState ?? "unknown").toLowerCase();
    const states = {
      up: ["↑", "Aufwärtsfahrt", "#2e7d32"],
      down: ["↓", "Abwärtsfahrt", "#1565c0"],
      stopped: ["■", "Steht", "var(--secondary-text-color)"],
      stop: ["■", "Steht", "var(--secondary-text-color)"],
      idle: ["■", "Steht", "var(--secondary-text-color)"],
    };
    const [icon, label, color] = states[raw] || ["?", this._elevatorState ?? "Unbekannt", "var(--secondary-text-color)"];
    return `<div class="elevator-state" title="Aufzugstatus: ${label}">
      <span class="elevator-icon" style="color:${color}">${icon}</span>
      <span><small>Aktueller Status</small><strong>${label}</strong></span>
    </div>`;
  }

  render() {
    const title = this.config?.title || "Globale LED-Konfiguration";
    if (this._error) {
      this.innerHTML = `<ha-card><div style="padding:12px"><b>${title}</b><p>${this._error}</p></div></ha-card>`;
      return;
    }
    if (!this._global || !this._colors) {
      this.innerHTML = `<ha-card><div style="padding:12px">${title}: Lade…</div></ha-card>`;
      return;
    }
    const offline = !this._device.available;
    const disabled = offline ? "disabled" : "";
    const effects = PICO_EFFECTS;
    const elevatorEffects = ["chevrons", "scanner", "theater"];

    this.innerHTML = `
      <ha-card>
        <style>
          .wrap { padding:14px; ${offline ? "opacity:.55" : ""} }
          h2 { font-size:18px; margin:0 0 10px; }
          h3 { font-size:14px; margin:0 0 8px; }
          .offline,.hint,.status { color:var(--secondary-text-color); font-size:11px; }
          .groups { display:grid; grid-template-columns:repeat(2,minmax(280px,1fr)); gap:12px; }
          .group { border:1px solid var(--divider-color); border-radius:10px; padding:10px; min-width:0; }
          .fields { display:grid; grid-template-columns:repeat(2,minmax(120px,1fr)); gap:8px; }
          .field { display:flex; flex-direction:column; gap:3px; min-width:0; font-size:11px; color:var(--secondary-text-color); }
          .field.full { grid-column:1 / -1; }
          select,input[type="number"],input[type="text"] { box-sizing:border-box; width:100%; min-height:34px; border:1px solid var(--divider-color); border-radius:7px; padding:6px 7px; background:var(--card-background-color); color:var(--primary-text-color); font:inherit; font-size:13px; }
          input[type="range"] { width:100%; }
          .toggle { display:flex; align-items:center; gap:8px; min-height:34px; color:var(--primary-text-color); font-size:13px; }
          .wheels { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
          .wheel-box { min-width:0; text-align:center; }
          .wheel-label { margin-bottom:3px; font-size:11px; font-weight:500; }
          .status { min-height:16px; margin-top:8px; }
          .elevator-state { display:flex; align-items:center; gap:9px; margin:0 0 10px; padding:7px 9px; border:1px solid var(--divider-color); border-radius:8px; background:var(--secondary-background-color); }
          .elevator-icon { font-size:26px; line-height:1; width:26px; text-align:center; font-weight:700; }
          .elevator-state span:last-child { display:flex; flex-direction:column; line-height:1.2; }
          .elevator-state small { color:var(--secondary-text-color); font-size:10px; }
          .elevator-state strong { color:var(--primary-text-color); font-size:13px; }
          details summary { cursor:pointer; font-size:14px; font-weight:600; margin-bottom:8px; }
          @media (max-width:760px) { .groups { grid-template-columns:1fr; } }
          @media (max-width:430px) { .fields { grid-template-columns:1fr; } .wheels { grid-template-columns:1fr 1fr; } }
        </style>
        <div class="wrap">
          <h2>${title}</h2>
          ${offline ? '<div class="offline">Nicht verfügbar</div>' : ""}
          <div class="groups">
            <section class="group">
              <h3>LED & Effekte</h3>
              <div class="fields">
                ${this.rangeField("brightness","Helligkeit",0,1,0.01)}
                ${this.selectField("effect","Standard-Effekt",effects)}
                ${this.numberField("effect_speed","Effektgeschwindigkeit",1,20,1)}
                ${this.numberField("effect_intensity","Effektintensität",0,1,0.05)}
                ${this.numberField("effect_delay_ms","Effekt-Verzögerung (ms)",0,1000,1)}
                ${this.rangeField("two_color_split","Zweifarben-Aufteilung",0,1,0.01)}
              </div>
            </section>

            <section class="group">
              <h3>Two Color</h3>
              <div class="wheels">
                <div class="wheel-box"><div class="wheel-label">Farbe 1</div><pico-rest-day-wheel compact data-target="color1"></pico-rest-day-wheel></div>
                <div class="wheel-box"><div class="wheel-label">Farbe 2</div><pico-rest-day-wheel compact data-target="color2"></pico-rest-day-wheel></div>
              </div>
            </section>

            <section class="group">
              <h3>Standort & Sonnenuntergang</h3>
              <div class="fields">
                ${this.checkboxField("use_sunset","Sonnenuntergang verwenden")}
                ${this.numberField("latitude","Breitengrad",-90,90,0.0001)}
                ${this.numberField("longitude","Längengrad",-180,180,0.0001)}
                ${this.textField("timezone","Zeitzone")}
              </div>
            </section>

            <section class="group">
              <h3>Aufzug</h3>
              ${this.elevatorStatusHtml()}
              <div class="fields">
                ${this.textField("elevator_url","Aufzug-URL",true)}
                ${this.selectField("elevator_effect","Aufzug-Effekt",elevatorEffects)}
                ${this.numberField("elevator_speed","Aufzug-Geschwindigkeit",1,20,1)}
                ${this.numberField("elevator_delay_ms","Aufzug-Verzögerung (ms)",0,1000,1)}
                ${this.numberField("elevator_poll_seconds","Abfrageintervall (s)",0.2,60,0.2)}
              </div>
            </section>

            <section class="group" style="grid-column:1/-1">
              <details>
                <summary>Erweiterte Hardware-/Legacy-Einstellungen</summary>
                <div class="fields">
                  ${this.numberField("led_pin","LED GPIO",0,29,1)}
                  ${this.numberField("led_count","LED-Anzahl",1,5000,1)}
                  ${this.checkboxField("special_mode","Special Mode (Legacy)")}
                </div>
              </details>
            </section>
          </div>
          <div class="status"></div>
        </div>
      </ha-card>`;

    for (const target of ["color1", "color2"]) {
      const wheel = this.querySelector(`pico-rest-day-wheel[data-target="${target}"]`);
      wheel.value = this._colors[target] || [255,255,255];
      if (!offline) wheel.addEventListener("color-change", (event) => this.saveColor(target,event.detail,true));
    }
    this.querySelectorAll("[data-config-key]").forEach((el) => {
      const key = el.dataset.configKey;
      const handler = () => {
        let value;
        if (el.type === "checkbox") value = el.checked;
        else if (el.type === "number" || el.type === "range") value = Number(el.value);
        else value = el.value;
        this.saveConfig(key,value);
      };
      el.addEventListener(el.type === "range" ? "change" : "change", handler);
    });
  }

  numberField(key,label,min,max,step) {
    return `<label class="field"><span>${label}</span><input data-config-key="${key}" type="number" min="${min}" max="${max}" step="${step}" value="${this.val(key)}" ${!this._device?.available ? "disabled" : ""}></label>`;
  }

  rangeField(key,label,min,max,step) {
    return `<label class="field"><span>${label}: ${this.val(key)}</span><input data-config-key="${key}" type="range" min="${min}" max="${max}" step="${step}" value="${this.val(key)}" ${!this._device?.available ? "disabled" : ""}></label>`;
  }

  textField(key,label,full=false) {
    return `<label class="field ${full ? "full" : ""}"><span>${label}</span><input data-config-key="${key}" type="text" value="${String(this.val(key)).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;')}" ${!this._device?.available ? "disabled" : ""}></label>`;
  }

  checkboxField(key,label) {
    return `<label class="field"><span>${label}</span><span class="toggle"><input data-config-key="${key}" type="checkbox" ${this.val(key,false) ? "checked" : ""} ${!this._device?.available ? "disabled" : ""}>${this.val(key,false) ? "Ein" : "Aus"}</span></label>`;
  }

  selectField(key,label,options) {
    const current=String(this.val(key));
    return `<label class="field"><span>${label}</span><select data-config-key="${key}" ${!this._device?.available ? "disabled" : ""}>${options.map((v)=>`<option value="${v}" ${v===current?"selected":""}>${v}</option>`).join("")}</select></label>`;
  }

  async saveConfig(key,value) {
    if (!this._device?.available) return;
    const status=this.querySelector('.status');
    if (status) status.textContent='Speichere…';
    this._saving=true;
    try {
      await this._hass.callWS({type:'pico_rest/set_led_config',entry_id:this._device.entry_id,key,value});
      this._global={...(this._global||{}),[key]:value};
      if (status) status.textContent='Gespeichert';
      setTimeout(()=>this.refreshFromBackend(),250);
    } catch(error) { if(status) status.textContent=`Fehler: ${error}`; }
    finally { this._saving=false; }
  }

  async saveColor(target,rgb,debounce=false) {
    if (!this._device?.available) return;
    this._colors={...(this._colors||{}),[target]:[...rgb]};
    if (debounce) {
      clearTimeout(this[`_${target}Timer`]);
      this[`_${target}Timer`]=setTimeout(()=>this.saveColorNow(target,rgb),350);
      return;
    }
    await this.saveColorNow(target,rgb);
  }

  async saveColorNow(target,rgb) {
    const status=this.querySelector('.status');
    if(status) status.textContent='Speichere…';
    this._saving=true;
    try {
      await this._hass.callWS({type:'pico_rest/set_led_color',entry_id:this._device.entry_id,target,rgb:[...rgb]});
      if(status) status.textContent='Gespeichert';
    } catch(error) { if(status) status.textContent=`Fehler: ${error}`; }
    finally { this._saving=false; }
  }
}

if (!customElements.get("pico-rest-led-config-card")) {
  customElements.define("pico-rest-led-config-card", PicoRestLedConfigCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "pico-rest-day-card")) {
  window.customCards.push({
    type: "pico-rest-day-card",
    name: "Pico REST Wochentag",
    description: "RGB-Farbe, Effekt sowie Ein- und Ausschaltzeit eines Pico-LED-Wochentags.",
    preview: false,
    documentationURL: "https://github.com/1waze/home-assistant-pico-rest",
  });
}


if (!window.customCards.some((card) => card.type === "pico-rest-led-config-card")) {
  window.customCards.push({
    type: "pico-rest-led-config-card",
    name: "Pico REST globale LED-Konfiguration",
    description: "Alle globalen Pico-LED-Konfigurationswerte inklusive RGB-Farben, Standort und Aufzug.",
    preview: false,
    documentationURL: "https://github.com/1waze/home-assistant-pico-rest",
  });
}
