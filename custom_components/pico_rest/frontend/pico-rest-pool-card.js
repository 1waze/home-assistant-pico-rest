class PicoRestPoolCard extends HTMLElement {
  connectedCallback() {
    this._startTimer();
  }

  disconnectedCallback() {
    this._stopTimer();
  }

  setConfig(config) {
    this.config = { title: "Poolsteuerung", hours_to_show: 8, ...config };
    this._loaded = false;
    if (this._hass) this._load();
  }

  set hass(hass) {
    this._hass = hass;
    this._startTimer();
    if (this.config && !this._loaded) this._load();
  }

  getCardSize() { return 10; }

  getGridOptions() {
    return { columns: 18, min_columns: 12 };
  }

  _startTimer() {
    if (this._timer) return;
    this._timer = setInterval(() => this._refresh(), 5000);
  }

  _stopTimer() {
    if (!this._timer) return;
    clearInterval(this._timer);
    this._timer = undefined;
  }

  async _call(type, data = {}) {
    return this._hass.callWS({ type, ...data });
  }

  _selectDevice(devices) {
    if (!Array.isArray(devices) || devices.length === 0) return null;
    if (this.config.entry_id) return devices.find((d) => d.entry_id === this.config.entry_id) || null;
    if (this.config.device_name) return devices.find((d) => d.name === this.config.device_name) || null;
    return devices[0];
  }

  async _load() {
    try {
      const devices = await this._call("pico_rest/pool_state");
      this._device = this._selectDevice(devices);
      if (!this._device) throw new Error("Kein Pico REST Pool-Controller gefunden");
      this._loaded = true;
      await this._loadHistory();
      this.render();
    } catch (err) {
      this._error = String(err);
      this.render();
    }
  }

  async _refresh() {
    if (!this._hass || !this.config || this._busy) return;
    try {
      const devices = await this._call("pico_rest/pool_state");
      const next = this._selectDevice(devices);
      if (!next) return;
      const changed = JSON.stringify(next) !== JSON.stringify(this._device);
      this._device = next;
      if (changed) this.render();
      if (!this._lastHistory || Date.now() - this._lastHistory > 60000) {
        await this._loadHistory();
        this.render();
      }
    } catch (_) { /* retain last values */ }
  }

  async _loadHistory() {
    if (!this._device?.entity_ids) return;
    const ids = [
      this._device.entity_ids.t_pool,
      this._device.entity_ids.t_collector,
      this._device.entity_ids.valve,
    ].filter(Boolean);
    if (!ids.length) return;
    const end = new Date();
    const start = new Date(end.getTime() - Number(this.config.hours_to_show || 8) * 3600000);
    try {
      const result = await this._call("history/history_during_period", {
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        entity_ids: ids,
        minimal_response: true,
        no_attributes: true,
      });
      this._history = this._normalizeHistory(result, ids);
      this._lastHistory = Date.now();
    } catch (_) {
      this._history = {};
    }
  }

  _normalizeHistory(result, ids) {
    const out = {};
    if (Array.isArray(result)) {
      result.forEach((series, idx) => { out[ids[idx]] = Array.isArray(series) ? series : []; });
    } else if (result && typeof result === "object") {
      ids.forEach((id) => { out[id] = Array.isArray(result[id]) ? result[id] : []; });
    }
    return out;
  }

  async _set(key, value) {
    if (!this._device || this._busy) return;
    this._busy = true;
    this._status = "Speichern …";
    this.render();
    try {
      await this._call("pico_rest/set_pool_value", {
        entry_id: this._device.entry_id,
        key,
        value,
      });
      this._status = "Gespeichert";
      await this._refresh();
    } catch (err) {
      this._status = `Fehler: ${err.message || err}`;
    } finally {
      this._busy = false;
      this.render();
      setTimeout(() => { this._status = ""; this.render(); }, 1800);
    }
  }

  _num(v, fallback = 0) {
    const n = Number(v);
    return Number.isFinite(n) ? n : fallback;
  }

  _fmt(v, digits = 1) {
    const n = Number(v);
    return Number.isFinite(n) ? n.toFixed(digits).replace(".", ",") : "–";
  }

  _tempGauge(label, value, min, max, cls) {
    const n = this._num(value, min);
    const pct = Math.max(0, Math.min(100, ((n - min) / (max - min)) * 100));
    return `<div class="temp ${cls}">
      <div class="temp-head"><span class="thermo">♨</span><span>${label}</span><strong>${this._fmt(value)}°C</strong></div>
      <div class="bar"><span style="width:${pct}%"></span></div>
      <div class="scale"><span>${min}</span><span>${max}</span></div>
    </div>`;
  }

  _slider(key, label, value, min, max, step) {
    return `<div class="slider-row">
      <label>${label}</label>
      <div class="slider-wrap">
        <input data-key="${key}" type="range" min="${min}" max="${max}" step="${step}" value="${this._num(value)}">
        <output>${this._fmt(value, step < 1 ? 1 : 0)}</output>
      </div>
    </div>`;
  }

  _chart() {
    const width = 760, height = 180, padL = 46, padR = 10, padT = 12, padB = 28;
    const poolId = this._device?.entity_ids?.t_pool;
    const collId = this._device?.entity_ids?.t_collector;
    const valveId = this._device?.entity_ids?.valve;
    const tempSeries = [
      { id: poolId, cls: "pool-line" },
      { id: collId, cls: "collector-line" },
    ].filter((item) => item.id && this._history?.[item.id]?.length);
    const valveHistory = valveId && this._history?.[valveId]?.length
      ? this._history[valveId]
      : [];
    if (!tempSeries.length && !valveHistory.length) {
      return `<div class="chart empty">Noch keine Verlaufsdaten geladen</div>`;
    }

    const now = Date.now();
    const start = now - Number(this.config.hours_to_show || 8) * 3600000;
    const values = [];
    tempSeries.forEach((item) => this._history[item.id].forEach((p) => {
      const v = Number(p.s ?? p.state);
      if (Number.isFinite(v)) values.push(v);
    }));
    let minY = Math.floor(Math.min(...values, 10) / 5) * 5;
    let maxY = Math.ceil(Math.max(...values, 35) / 5) * 5;
    if (maxY <= minY) maxY = minY + 5;
    const x = (t) => padL + ((t - start) / (now - start)) * (width - padL - padR);
    const y = (v) => padT + (1 - (v - minY) / (maxY - minY)) * (height - padT - padB);
    const pointTime = (p) => p.lu
      ? p.lu * 1000
      : new Date(p.last_updated || p.last_changed || Date.now()).getTime();
    const pathFor = (arr) => {
      let index = 0;
      return arr.map((p) => {
        const v = Number(p.s ?? p.state);
        if (!Number.isFinite(v)) return "";
        const cmd = index++ ? "L" : "M";
        return `${cmd}${x(pointTime(p)).toFixed(1)},${y(v).toFixed(1)}`;
      }).filter(Boolean).join(" ");
    };
    const valvePath = (arr) => {
      const points = arr.map((p) => {
        const raw = String(p.s ?? p.state ?? "").toLowerCase();
        if (!["on", "off", "true", "false", "1", "0"].includes(raw)) return null;
        const on = ["on", "true", "1"].includes(raw);
        return { x: x(pointTime(p)), y: y(on ? maxY : minY) };
      }).filter(Boolean);
      if (!points.length) return "";
      let d = `M${points[0].x.toFixed(1)},${points[0].y.toFixed(1)}`;
      for (let i = 1; i < points.length; i++) {
        d += ` H${points[i].x.toFixed(1)} V${points[i].y.toFixed(1)}`;
      }
      d += ` H${x(now).toFixed(1)}`;
      return d;
    };

    const grid = [];
    for (let v = minY; v <= maxY; v += 5) {
      const yy = y(v); grid.push(`<line x1="${padL}" y1="${yy}" x2="${width-padR}" y2="${yy}"/><text x="4" y="${yy+4}">${v}</text>`);
    }
    const hours = Math.max(1, Math.round(Number(this.config.hours_to_show || 8)));
    const labels = [];
    for (let i = 0; i <= hours; i += Math.max(1, Math.ceil(hours / 8))) {
      const t = start + i * 3600000; const xx = x(t); const d = new Date(t);
      labels.push(`<line x1="${xx}" y1="${padT}" x2="${xx}" y2="${height-padB}"/><text x="${xx}" y="${height-7}" text-anchor="middle">${String(d.getHours()).padStart(2,"0")}:00</text>`);
    }
    return `<div class="chart"><svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      <g class="grid">${grid.join("")}${labels.join("")}</g>
      ${tempSeries.map((item) => `<path class="${item.cls}" d="${pathFor(this._history[item.id])}"/>`).join("")}
      ${valveHistory.length ? `<path class="valve-line" d="${valvePath(valveHistory)}"/>` : ""}
    </svg></div>`;
  }

  _picoTime(value) {
    if (!Array.isArray(value) || value.length < 6) return "–";
    const [Y,M,D,h,m,s] = value;
    return `${Y}-${String(M).padStart(2,"0")}-${String(D).padStart(2,"0")} ${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
  }

  render() {
    if (!this.config) return;
    if (this._error) {
      this.innerHTML = `<ha-card><div class="err">${this._error}</div></ha-card>`;
      return;
    }
    if (!this._device) {
      this.innerHTML = `<ha-card><div class="loading">Poolsteuerung wird geladen …</div></ha-card>`;
      return;
    }
    const s = this._device.status || {};
    const c = this._device.config || {};
    const manual = String(c.mode ?? s.mode) === "manual";
    const auto = !manual;
    const pump = Boolean(s.pump);
    const valve = Boolean(s.valve);
    const clean = Boolean(c.clean_mode ?? s.clean_mode);

    this.innerHTML = `<ha-card>
      <style>
        ha-card { padding:18px; overflow:hidden; }
        .top { display:grid; grid-template-columns:1fr 1fr; gap:28px; }
        .temp-head { display:grid; grid-template-columns:34px 1fr auto; align-items:center; gap:6px; font-size:22px; }
        .temp-head strong { font-size:31px; font-weight:400; }
        .thermo { font-size:31px; }
        .pool .bar span, .pool-line { stroke:#00bcd4; background:#00bcd4; }
        .collector .bar span, .collector-line { stroke:#f00; background:#f00; }
        .valve-line { stroke:#ffeb00; }
        .bar { height:4px; background:var(--divider-color); margin:3px 0 0 40px; }
        .bar span { display:block; height:100%; }
        .scale { margin-left:40px; display:flex; justify-content:space-between; font-size:10px; }
        .controls { display:grid; grid-template-columns:1fr 1fr; gap:28px; margin-top:22px; }
        .left-controls, .right-controls { display:grid; gap:12px; align-content:start; }
        .slider-row { display:grid; grid-template-columns:140px 1fr; align-items:center; gap:10px; }
        .slider-wrap { display:grid; grid-template-columns:1fr 38px; align-items:center; gap:8px; }
        input[type=range] { width:100%; accent-color:var(--primary-color); }
        output { width:34px; height:34px; border-radius:50%; background:var(--primary-color); color:#fff; display:grid; place-items:center; font-size:12px; }
        .switch-row { display:grid; grid-template-columns:1fr auto; align-items:center; min-height:38px; }
        .toggle { width:42px; height:24px; border-radius:12px; background:#666; position:relative; cursor:pointer; }
        .toggle::after { content:""; position:absolute; width:20px; height:20px; top:2px; left:2px; background:#fff; border-radius:50%; transition:.15s; }
        .toggle.on { background:var(--primary-color); }.toggle.on::after { left:20px; }
        .actor { font-size:18px; display:grid; grid-template-columns:1fr auto; align-items:center; min-height:38px; }
        .actor strong { font-size:30px; line-height:1; width:34px; text-align:center; cursor:pointer; user-select:none; }
        .pump-icon.on { color:var(--primary-color); }
        .pump-icon.off { color:var(--secondary-text-color); }
        .pump-icon.spinning { animation:pico-pump-spin 1.25s linear infinite; }
        .valve-icon.sun { color:#ffd600; }
        .valve-icon.snow { color:#80d8ff; }
        @keyframes pico-pump-spin { to { transform:rotate(360deg); } }
        @media (prefers-reduced-motion: reduce) { .pump-icon.spinning { animation:none; } }
        .manual-note { color:var(--secondary-text-color); font-size:11px; }
        .chart { margin-top:24px; height:185px; }.chart svg { width:100%; height:100%; }
        .chart .grid line { stroke:var(--divider-color); stroke-width:1; }.chart .grid text { fill:var(--secondary-text-color); font-size:11px; }
        .chart path { fill:none; stroke-width:3; vector-effect:non-scaling-stroke; }.chart.empty { display:grid; place-items:center; color:var(--secondary-text-color); border-top:1px solid var(--divider-color); }
        .times { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px; }
        .time-field { display:grid; gap:3px; font-size:11px; color:var(--secondary-text-color); }.time-field input { font-size:17px; padding:8px; border:0; border-bottom:1px solid var(--primary-color); background:transparent; color:var(--primary-text-color); }
        .diag { margin-top:18px; padding-top:14px; border-top:1px solid var(--divider-color); display:grid; grid-template-columns:repeat(4,1fr); gap:14px; align-items:center; text-align:center; }
        .diag strong { display:block; margin-top:5px; }.cpu { font-size:25px; }.quality { font-size:18px; }.meta { font-size:13px; }
        .status { min-height:18px; margin-top:8px; color:var(--secondary-text-color); font-size:11px; text-align:right; }
        .err,.loading { padding:20px; }
        @media(max-width:760px){ .top,.controls,.times { grid-template-columns:1fr; }.diag{grid-template-columns:1fr 1fr}.slider-row{grid-template-columns:115px 1fr}.temp-head{font-size:18px}.temp-head strong{font-size:25px} }
      </style>
      <div class="top">
        ${this._tempGauge("Pool", s.t_pool, 0, 40, "pool")}
        ${this._tempGauge("Absorber", s.t_collector, -20, 80, "collector")}
      </div>
      <div class="controls">
        <div class="left-controls">
          ${this._slider("target_temp", "Zieltemp.", c.target_temp, 5, 40, .5)}
          ${this._slider("diff_on", "Einschalt-Delta", c.diff_on, 0, 30, .5)}
          ${this._slider("diff_off", "Ausschalt-Delta", c.diff_off, 0, 30, .5)}
        </div>
        <div class="right-controls">
          <div class="switch-row"><span>Automatik</span><span class="toggle ${auto ? "on" : ""}" data-mode></span></div>
          <div class="switch-row"><span>Reinigung</span><span class="toggle ${clean ? "on" : ""}" data-clean></span></div>
          <div class="actor"><span>Pumpe</span><strong class="pump-icon ${pump ? "on spinning" : "off"}" data-pump title="Pumpe ${pump ? "Ein" : "Aus"}">⚙</strong></div>
          <div class="actor"><span>Ventil</span><strong class="valve-icon ${valve ? "sun" : "snow"}" data-valve title="Ventil ${valve ? "Ein" : "Aus"}">${valve ? "☀" : "❄"}</strong></div>
          <div class="manual-note">Pumpe/Ventil sind nur im manuellen Modus schaltbar.</div>
        </div>
      </div>
      ${this._chart()}
      <div class="times">
        <label class="time-field">Einschaltzeit<input data-time="pump_on" type="time" value="${c.pump_on || ""}"></label>
        <label class="time-field">Ausschaltzeit<input data-time="pump_off" type="time" value="${c.pump_off || ""}"></label>
      </div>
      <div class="diag">
        <div><span>CPU temp</span><strong class="cpu">${this._fmt(s.t_cpu)}°C</strong></div>
        <div><span>WiFi</span><strong class="quality">${s.wifi_quality ?? "–"}</strong><small>${s.wifi_rssi ?? "–"} dBm</small></div>
        <div class="meta"><span>Pico-Zeit</span><strong>${this._picoTime(s.time)}</strong><span>Free Memory</span><strong>${s.free_mem ?? "–"} B</strong></div>
        <div class="meta"><span>Version</span><strong>${s.version ?? "–"}</strong><span>IP</span><strong>${s.ip ?? "–"}</strong></div>
      </div>
      <div class="status">${this._status || ""}</div>
    </ha-card>`;

    this.querySelectorAll('input[type="range"]').forEach((el) => {
      el.addEventListener("input", () => { el.nextElementSibling.textContent = this._fmt(el.value, .5 < 1 ? 1 : 0); });
      el.addEventListener("change", () => this._set(el.dataset.key, Number(el.value)));
    });
    this.querySelector("[data-mode]")?.addEventListener("click", () => this._set("mode", auto ? "manual" : "auto"));
    this.querySelector("[data-clean]")?.addEventListener("click", () => this._set("clean_mode", !clean));
    this.querySelector("[data-pump]")?.addEventListener("click", () => { if (manual) this._set("manual_pump", !Boolean(s.manual_pump)); });
    this.querySelector("[data-valve]")?.addEventListener("click", () => { if (manual) this._set("manual_valve", !Boolean(s.manual_valve)); });
    this.querySelectorAll("[data-time]").forEach((el) => el.addEventListener("change", () => this._set(el.dataset.time, el.value)));
  }
}

if (!customElements.get("pico-rest-pool-card")) {
  customElements.define("pico-rest-pool-card", PicoRestPoolCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "pico-rest-pool-card")) {
  window.customCards.push({
    type: "pico-rest-pool-card",
    name: "Pico REST Pool Card",
    description: "Steuerung und Visualisierung eines Pico REST Pool-Controllers",
    preview: true,
  });
}
