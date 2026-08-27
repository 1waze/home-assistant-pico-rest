const DAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];

function rgbToHex(rgb) {
  return `#${rgb.map((v) => Number(v).toString(16).padStart(2, "0")).join("")}`;
}

function hsvToRgb(h, s, v) {
  const c = v * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = v - c;
  let r = 0, g = 0, b = 0;
  if (h < 60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];
  return [r, g, b].map((n) => Math.round((n + m) * 255));
}

function rgbToHsv([r, g, b]) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
  let h = 0;
  if (d) {
    if (max === r) h = 60 * (((g - b) / d) % 6);
    else if (max === g) h = 60 * ((b - r) / d + 2);
    else h = 60 * ((r - g) / d + 4);
  }
  if (h < 0) h += 360;
  return [h, max === 0 ? 0 : d / max, max];
}

class PicoColorWheel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.rgb = [255, 255, 255];
    this.hsv = [0, 0, 1];
  }
  connectedCallback() { this.render(); }
  set value(rgb) { this.rgb = [...rgb]; this.hsv = rgbToHsv(this.rgb); if (this.isConnected) this.render(); }
  get value() { return this.rgb; }
  render() {
    const [h, s, v] = this.hsv;
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;width:260px;max-width:80vw;font-family:var(--paper-font-body1_-_font-family, sans-serif)}
        canvas{width:240px;height:240px;display:block;margin:auto;touch-action:none;cursor:crosshair}
        .row{display:flex;align-items:center;gap:10px;margin-top:12px}.row input{flex:1}
        .swatch{width:34px;height:34px;border-radius:50%;border:1px solid var(--divider-color);background:${rgbToHex(this.rgb)}}
        .value{text-align:center;margin-top:8px;font-variant-numeric:tabular-nums}
      </style>
      <canvas width="240" height="240"></canvas>
      <div class="row"><span>Helligkeit</span><input type="range" min="0" max="100" value="${Math.round(v * 100)}"><span class="swatch"></span></div>
      <div class="value">RGB ${this.rgb.join(", ")} · ${rgbToHex(this.rgb).toUpperCase()}</div>`;
    const canvas = this.shadowRoot.querySelector("canvas");
    this.drawWheel(canvas, h, s);
    const pick = (ev) => {
      const rect = canvas.getBoundingClientRect();
      const scale = canvas.width / rect.width;
      const x = (ev.clientX - rect.left) * scale - canvas.width / 2;
      const y = (ev.clientY - rect.top) * scale - canvas.height / 2;
      const radius = canvas.width / 2 - 8;
      const dist = Math.min(radius, Math.hypot(x, y));
      let hue = Math.atan2(y, x) * 180 / Math.PI + 90;
      if (hue < 0) hue += 360;
      this.hsv = [hue, dist / radius, this.hsv[2]];
      this.rgb = hsvToRgb(...this.hsv);
      this.render();
      this.dispatchEvent(new CustomEvent("color-change", { detail: this.rgb, bubbles: true, composed: true }));
    };
    canvas.addEventListener("pointerdown", (ev) => { canvas.setPointerCapture(ev.pointerId); pick(ev); });
    canvas.addEventListener("pointermove", (ev) => { if (canvas.hasPointerCapture(ev.pointerId)) pick(ev); });
    this.shadowRoot.querySelector('input[type="range"]').addEventListener("input", (ev) => {
      this.hsv[2] = Number(ev.target.value) / 100;
      this.rgb = hsvToRgb(...this.hsv);
      this.render();
      this.dispatchEvent(new CustomEvent("color-change", { detail: this.rgb, bubbles: true, composed: true }));
    });
  }
  drawWheel(canvas, selectedHue, selectedSat) {
    const ctx = canvas.getContext("2d");
    const cx = canvas.width / 2, cy = canvas.height / 2, radius = cx - 8;
    const image = ctx.createImageData(canvas.width, canvas.height);
    for (let y = 0; y < canvas.height; y++) for (let x = 0; x < canvas.width; x++) {
      const dx = x - cx, dy = y - cy, d = Math.hypot(dx, dy);
      const i = (y * canvas.width + x) * 4;
      if (d <= radius) {
        let hue = Math.atan2(dy, dx) * 180 / Math.PI + 90; if (hue < 0) hue += 360;
        const rgb = hsvToRgb(hue, d / radius, 1);
        image.data[i] = rgb[0]; image.data[i+1] = rgb[1]; image.data[i+2] = rgb[2]; image.data[i+3] = 255;
      }
    }
    ctx.putImageData(image, 0, 0);
    const angle = (selectedHue - 90) * Math.PI / 180;
    const rr = selectedSat * radius;
    const px = cx + Math.cos(angle) * rr, py = cy + Math.sin(angle) * rr;
    ctx.beginPath(); ctx.arc(px, py, 7, 0, Math.PI * 2); ctx.lineWidth = 3; ctx.strokeStyle = "white"; ctx.stroke();
    ctx.beginPath(); ctx.arc(px, py, 9, 0, Math.PI * 2); ctx.lineWidth = 1; ctx.strokeStyle = "black"; ctx.stroke();
  }
}
customElements.define("pico-color-wheel", PicoColorWheel);

class PicoRestColorPanel extends HTMLElement {
  set hass(hass) { this._hass = hass; if (!this._loaded) this.load(); }
  set panel(panel) { this._panel = panel; }
  async load() {
    if (!this._hass) return;
    this._loaded = true;
    try { this.devices = await this._hass.callWS({ type: "pico_rest/led_colors" }); }
    catch (err) { this.error = String(err); }
    this.render();
  }
  render() {
    this.innerHTML = `
      <style>
        pico-rest-color-panel{display:block;padding:24px;max-width:1100px;margin:auto;color:var(--primary-text-color)}
        .head{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}h1{font-size:24px;margin:0}
        .device{background:var(--ha-card-background,var(--card-background-color));border-radius:var(--ha-card-border-radius,12px);box-shadow:var(--ha-card-box-shadow);padding:20px;margin-bottom:20px}
        .device h2{margin:0 0 16px;font-size:20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}
        button.color{display:flex;align-items:center;gap:12px;width:100%;padding:12px;border:1px solid var(--divider-color);border-radius:10px;background:transparent;color:var(--primary-text-color);cursor:pointer;text-align:left;font-size:14px}
        .dot{width:32px;height:32px;border-radius:50%;border:1px solid var(--divider-color);flex:none}.meta{opacity:.7;font-size:12px}.offline{opacity:.55}
        dialog{border:0;border-radius:16px;background:var(--ha-card-background,var(--card-background-color));color:var(--primary-text-color);padding:20px;box-shadow:0 10px 40px #0008}
        dialog::backdrop{background:#0008}.dlghead{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.dlghead h3{margin:0}.close{border:0;background:transparent;color:inherit;font-size:24px;cursor:pointer}
        .save{margin-top:16px;width:100%;padding:10px;border:0;border-radius:8px;background:var(--primary-color);color:var(--text-primary-color,#fff);font-weight:600;cursor:pointer}
      </style>
      <div class="head"><h1>Pico REST · LED-Farben</h1></div>
      ${this.error ? `<div>${this.error}</div>` : (this.devices || []).map((d) => this.deviceHtml(d)).join("")}
      <dialog><div class="dlghead"><h3></h3><button class="close">×</button></div><pico-color-wheel></pico-color-wheel><button class="save">Übernehmen</button></dialog>`;
    this.querySelectorAll("button.color").forEach((btn) => btn.addEventListener("click", () => this.openPicker(btn.dataset.entry, btn.dataset.target, btn.dataset.label)));
    const dialog = this.querySelector("dialog");
    dialog.querySelector(".close").onclick = () => dialog.close();
    dialog.querySelector(".save").onclick = () => this.savePicker();
  }
  deviceHtml(d) {
    const items = [["color1","Farbe 1"],["color2","Farbe 2"], ...DAYS.map((name, i) => [`day_${i}`, `${name} Farbe`])];
    return `<section class="device ${d.available ? "" : "offline"}"><h2>${d.name}${d.available ? "" : " · nicht verfügbar"}</h2><div class="grid">${items.map(([key,label]) => {
      const rgb = d.colors[key] || [0,0,0];
      return `<button class="color" data-entry="${d.entry_id}" data-target="${key}" data-label="${label}" ${d.available ? "" : "disabled"}><span class="dot" style="background:${rgbToHex(rgb)}"></span><span><b>${label}</b><br><span class="meta">RGB ${rgb.join(", ")}</span></span></button>`;
    }).join("")}</div></section>`;
  }
  openPicker(entryId, target, label) {
    this._edit = { entryId, target };
    const d = this.devices.find((x) => x.entry_id === entryId);
    const dialog = this.querySelector("dialog");
    dialog.querySelector("h3").textContent = label;
    dialog.querySelector("pico-color-wheel").value = d.colors[target];
    dialog.showModal();
  }
  async savePicker() {
    const dialog = this.querySelector("dialog"), wheel = dialog.querySelector("pico-color-wheel"), save = dialog.querySelector(".save");
    save.disabled = true; save.textContent = "Speichere…";
    try {
      await this._hass.callWS({ type: "pico_rest/set_led_color", entry_id: this._edit.entryId, target: this._edit.target, rgb: wheel.value });
      dialog.close(); this._loaded = false; await this.load();
    } catch (err) { alert(`Pico REST: ${err}`); }
    finally { save.disabled = false; save.textContent = "Übernehmen"; }
  }
}
customElements.define("pico-rest-color-panel", PicoRestColorPanel);
