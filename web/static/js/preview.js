/**
 * Discord Embed Simulator — live preview for guild settings.
 * Expects elements with IDs: sim-title, sim-desc, sim-color,
 * sim-color-bar, sim-bot-name, sim-timestamp.
 */
(function () {
  const $ = (s) => document.querySelector(s);

  const titleEl = $("#sim-title");
  const descEl = $("#sim-desc");
  const colorInput = $("#embed_color");
  const colorBar = $("#sim-color-bar");
  const embedTitle = $("#embed-title");
  const embedDesc = $("#embed-desc");
  const embedFooter = $("#embed-footer");
  const timestampEl = $("#sim-timestamp");

  if (!colorInput) return;

  function now() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const months = [
      "Jan","Feb","Mar","Apr","May","Jun",
      "Jul","Aug","Sep","Oct","Nov","Dec",
    ];
    return `${months[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  function sync() {
    const color = colorInput.value || "#6366f1";
    if (colorBar) colorBar.style.background = color;
    if (embedTitle) embedTitle.textContent = titleEl ? titleEl.value || "Заголовок ембеда" : "";
    if (embedDesc) embedDesc.textContent = descEl ? descEl.value || "Опис ембеда..." : "";
    if (timestampEl) timestampEl.textContent = now();
  }

  colorInput.addEventListener("input", sync);
  if (titleEl) titleEl.addEventListener("input", sync);
  if (descEl) descEl.addEventListener("input", sync);

  sync();
})();
