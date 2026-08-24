import { selectTrackedClosePreview } from "/preview-state.js";

const state = { csrf: "", data: null, preview: null, range: "all" };
const $ = (selector) => document.querySelector(selector);
const h = (value) => String(value ?? "—").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
const money = (value, currency = "EUR") => value === null || value === undefined ? "N/A" : new Intl.NumberFormat("fr-FR", { style: "currency", currency, maximumFractionDigits: 0, signDisplay: "exceptZero" }).format(Number(value));
const amount = (value, currency = "EUR") => value === null || value === undefined ? "N/A" : new Intl.NumberFormat("fr-FR", { style: "currency", currency, maximumFractionDigits: 0 }).format(Number(value));
const percent = (value) => value === null || value === undefined ? "N/A" : new Intl.NumberFormat("fr-FR", { style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" }).format(Number(value));
const age = (timestamp) => {
  if (!timestamp) return "N/A";
  const seconds = Math.max(0, Math.round((Date.now() - Date.parse(timestamp)) / 1000));
  if (seconds < 60) return `${seconds} sec ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`;
  return `${Math.floor(seconds / 86400)} d ago`;
};

async function api(path, options = {}) {
  const headers = { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) };
  if (options.method && options.method !== "GET") headers["X-CSRF-Token"] = state.csrf;
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) { window.location.assign("/"); throw new Error("UNAUTHORIZED"); }
  const payload = response.headers.get("Content-Type")?.includes("json") ? await response.json() : null;
  if (!response.ok) { const error = new Error(payload?.error || `HTTP_${response.status}`); error.status = response.status; throw error; }
  return payload;
}

function setEconomicValue(selector, value, format = money) {
  const element = $(selector);
  element.textContent = format(value);
  element.classList.toggle("positive", value !== null && Number(value) > 0);
  element.classList.toggle("negative", value !== null && Number(value) < 0);
}

function dlRows(rows) {
  return rows.map(([term, value, source]) => `<dt>${h(term)}${source ? `<small> · ${h(source)}</small>` : ""}</dt><dd>${h(value)}</dd>`).join("");
}

function renderChart(history) {
  const svg = $("#pnl-chart");
  const cutoff = state.range === "today" ? Date.now() - 86400000 : state.range === "7d" ? Date.now() - 7 * 86400000 : 0;
  const points = history.filter((row) => Date.parse(row.timestamp) >= cutoff).slice().reverse();
  if (!points.length) { svg.innerHTML = `<text x="300" y="110" fill="#9aa8b7" text-anchor="middle">No persisted PnL snapshot</text>`; return; }
  const values = points.flatMap((point) => [Number(point.mtm_pnl), point.liquidation_pnl === null ? Number(point.mtm_pnl) : Number(point.liquidation_pnl)]);
  const minimum = Math.min(...values, 0); const maximum = Math.max(...values, 0); const span = Math.max(maximum - minimum, 1);
  const coordinates = (field) => points.map((point, index) => {
    const value = point[field] === null ? Number(point.mtm_pnl) : Number(point[field]);
    return `${30 + index * 540 / Math.max(points.length - 1, 1)},${195 - (value - minimum) / span * 165}`;
  }).join(" ");
  const zeroY = 195 - (0 - minimum) / span * 165;
  svg.innerHTML = `<line x1="30" y1="${zeroY}" x2="570" y2="${zeroY}" stroke="#293444"/><polyline points="${coordinates("mtm_pnl")}" fill="none" stroke="#71b7ff" stroke-width="3"/><polyline points="${coordinates("liquidation_pnl")}" fill="none" stroke="#41d69a" stroke-width="3"/><text x="35" y="22" fill="#9aa8b7">${h(money(maximum))}</text><text x="35" y="214" fill="#9aa8b7">${h(money(minimum))}</text>`;
}

function render(data) {
  state.data = data; state.csrf = data.csrf_token;
  const system = data.system || {};
  $("#monitor-status").textContent = system.monitoring_paused ? "PAUSED" : data.position ? "RUNNING" : "IDLE";
  $("#market-status").textContent = system.market_data_status || "NOT_CONFIGURED";
  $("#last-monitor").textContent = age(system.last_monitor_run);
  $("#free-tier").textContent = system.conservation_mode ? "CONSERVATION" : data.usage_estimate.internalBudgetStatus;
  $("#conservation-banner").classList.toggle("hidden", !system.conservation_mode);
  $("#safe-mode").textContent = system.safe_mode ? "DISABLE SAFE MODE" : "SAFE MODE";
  $("#monitor-toggle").textContent = system.monitoring_paused ? "RESUME MONITORING" : "PAUSE MONITORING";
  const noPosition = !data.position;
  $("#empty-state").classList.toggle("hidden", !noPosition);
  $("#dashboard-content").classList.toggle("hidden", noPosition);
  if (noPosition) return;
  const position = data.position; const dossier = position.canonical_dossier; const pnl = data.latest_pnl;
  const currency = position.policy_currency;
  $("#demo-banner").classList.toggle("hidden", dossier.fixture_status !== "SYNTHETIC_DEMO");
  $("#position-state").textContent = position.state;
  $("#structure-name").textContent = position.structure_name;
  $("#remaining-quantity").textContent = `${position.quantity_remaining} / ${position.quantity_initial} remaining`;
  $("#structure-legs").textContent = dossier.legs.map((leg) => `${leg.side === "LONG" ? "+" : "−"}${leg.ratio * position.quantity_remaining} ${leg.option_right} ${leg.strike} · ${leg.expiration.slice(0, 10)}`).join("  |  ");
  $("#invested").textContent = amount(position.entry_cash, currency);
  setEconomicValue("#mtm-pnl", pnl?.mtm_pnl, (value) => money(value, currency));
  $("#mtm-return").textContent = percent(pnl?.mtm_return);
  setEconomicValue("#liquidation-pnl", pnl?.liquidation_pnl, (value) => money(value, currency));
  $("#liquidation-return").textContent = percent(pnl?.liquidation_return);
  $("#mark-value").textContent = amount(pnl?.market_value_policy, currency);
  $("#liquidation-value").textContent = amount(pnl?.liquidation_value, currency);
  $("#realized-pnl").textContent = money(position.realized_pnl, currency);
  const totalPnl = position.realized_pnl === null ? pnl?.mtm_pnl : Number(position.realized_pnl) + Number(pnl?.mtm_pnl ?? 0);
  $("#total-pnl").textContent = money(totalPnl, currency);
  $("#liquidation-mode").textContent = pnl?.liquidation_estimate_mode || "N/A";
  const model = dossier.latest_promoted_model_snapshot;
  setEconomicValue("#expected-pnl", model?.expected_remaining_pnl, (value) => money(value, currency));
  const modelAge = model ? age(model.timestamp) : "N/A — no promoted model snapshot";
  $("#model-age").textContent = model ? `Model snapshot ${model.timestamp} · ${modelAge}${Date.now() - Date.parse(model.timestamp) > 86400000 ? " · STALE MODEL SNAPSHOT" : ""}` : modelAge;
  $("#market-source").textContent = pnl?.provider || "NONE";
  $("#last-quote").textContent = age(pnl?.timestamp);
  const minDte = Math.min(...dossier.expirations.map((date) => Math.ceil((Date.parse(date) - Date.now()) / 86400000)));
  const initialIv = Object.values(dossier.initial_iv).reduce((sum, value) => sum + value, 0) / Object.values(dossier.initial_iv).length;
  const flat = dossier.flat_spot_diagnostics;
  const liveSource = pnl?.provider === "SYNTHETIC_DEMO" ? "SYNTHETIC DEMO" : "LIVE PROVIDER";
  $("#market-panel").innerHTML = dlRows([
    ["TTWO spot", pnl ? String(pnl.spot) : "N/A", pnl ? liveSource : "N/A"],
    ["DTE", String(minDte), "CLOCK"],
    ["IV", pnl?.iv == null ? "N/A" : percent(pnl.iv), pnl?.iv == null ? "N/A" : liveSource],
    ["IV change since entry", pnl?.iv == null ? "N/A" : percent(pnl.iv - initialIv), pnl?.iv == null ? "N/A" : liveSource],
    ["Net theta today", pnl?.theta == null ? "N/A" : String(pnl.theta), pnl?.theta == null ? "N/A" : liveSource],
    ["Flat Spot +7d", flat?.flat_spot_7d == null ? "N/A" : money(flat.flat_spot_7d, currency), flat ? `CANONICAL · ${age(flat.timestamp)}` : "N/A"],
    ["Flat Spot +30d", flat?.flat_spot_30d == null ? "N/A" : money(flat.flat_spot_30d, currency), flat ? `CANONICAL · ${age(flat.timestamp)}` : "N/A"],
    ["Flat Spot +60d", flat?.flat_spot_60d == null ? "N/A" : money(flat.flat_spot_60d, currency), flat ? `CANONICAL · ${age(flat.timestamp)}` : "N/A"],
    ["Flat Spot +90d", flat?.flat_spot_90d == null ? "N/A" : money(flat.flat_spot_90d, currency), flat ? `CANONICAL · ${age(flat.timestamp)}` : "N/A"],
  ]);
  const loss = model?.loss_probabilities || {};
  let liveGreeks = null;
  try { liveGreeks = pnl?.greeks_json ? JSON.parse(pnl.greeks_json) : null; } catch { liveGreeks = null; }
  const greeks = liveGreeks && Object.keys(liveGreeks).length ? liveGreeks : dossier.initial_greeks;
  const greekSource = liveGreeks && Object.keys(liveGreeks).length ? liveSource : "CANONICAL ENTRY SNAPSHOT";
  $("#risk-panel").innerHTML = dlRows([
    ["P(profit)", model?.probability_profit == null ? "N/A" : percent(model.probability_profit), model ? "LATEST MODEL SNAPSHOT" : "N/A"],
    ["P(loss >25%)", loss.loss_25 == null ? "N/A" : percent(loss.loss_25), model ? "LATEST MODEL SNAPSHOT" : "N/A"],
    ["P(loss >50%)", loss.loss_50 == null ? "N/A" : percent(loss.loss_50), model ? "LATEST MODEL SNAPSHOT" : "N/A"],
    ["P(loss >70%)", loss.loss_70 == null ? "N/A" : percent(loss.loss_70), model ? "LATEST MODEL SNAPSHOT" : "N/A"],
    ["VaR95", model?.var_95 == null ? "N/A" : money(model.var_95, currency), model ? "LATEST MODEL SNAPSHOT" : "N/A"],
    ["CVaR95", model?.cvar_95 == null ? "N/A" : money(model.cvar_95, currency), model ? "LATEST MODEL SNAPSHOT" : "N/A"],
    ...["delta", "gamma", "theta", "vega", "rho", "vanna", "vomma"].map((key) => [key[0].toUpperCase() + key.slice(1), greeks[key] ?? "N/A", greekSource]),
  ]);
  $("#engine-action").textContent = pnl?.monitor_action || "BLOCKED_INSUFFICIENT_DATA";
  $("#engine-reason").textContent = pnl ? `${pnl.data_freshness} · ${pnl.provider}` : "No monitoring snapshot.";
  const scores = dossier.five_scores;
  $("#scores").innerHTML = scores ? ["opportunity", "risk", "evidence", "model_agreement", "execution_quality"].map((key) => `<div class="score"><span>${h(key.replaceAll("_", " "))}</span><strong>${h(scores[key].score_value)}</strong><small>${h(Math.round(scores[key].coverage * 100))}% coverage</small></div>`).join("") : "N/A — no canonical five-score snapshot";
  renderChart(data.pnl_history);
  const events = [...data.audit_events, ...data.monitoring_events].sort((left, right) => String(right.timestamp).localeCompare(String(left.timestamp))).slice(0, 30);
  $("#events").innerHTML = events.map((event) => `<li><time>${h(new Date(event.timestamp).toLocaleString("fr-FR"))}</time><strong>${h(event.event_type)}</strong></li>`).join("") || "<li>No event</li>";
  const actionablePreview = data.close_previews.find((preview) => ["ACKNOWLEDGED", "RECONCILIATION_REQUIRED"].includes(preview.status));
  state.preview = selectTrackedClosePreview(data.close_previews);
  $("#manual-close-reported").classList.toggle("hidden", actionablePreview?.status !== "ACKNOWLEDGED");
  $("#close-status").textContent = actionablePreview ? `${actionablePreview.status} · ${actionablePreview.preview_id}` : "";
  if (position.state === "CLOSED") {
    $("#structure-name").textContent = "TTWO — CLOSED";
    $("#mtm-pnl").textContent = "N/A — CLOSED";
    $("#liquidation-pnl").textContent = "N/A — CLOSED";
    $("#total-pnl").textContent = money(position.realized_pnl, currency);
  }
  $("#close-structure").disabled = !pnl || pnl.liquidation_pnl === null || ["RECONCILIATION_REQUIRED", "CLOSED", "CANCELLED"].includes(position.state);
}

async function refresh() { try { render(await api("/api/dashboard")); } catch (error) { console.error(error); } }

async function mutation(path, body = {}) { const result = await api(path, { method: "POST", body: JSON.stringify(body) }); await refresh(); return result; }

$("#dossier-file").addEventListener("change", async (event) => {
  const file = event.target.files[0]; if (!file) return;
  try { await mutation("/api/positions/import", JSON.parse(await file.text())); } catch (error) { alert(error.message); }
});
$("#demo-import").addEventListener("click", () => mutation("/api/demo/import").catch((error) => alert(error.message)));
$("#safe-mode").addEventListener("click", () => mutation("/api/safe-mode", { enabled: !Boolean(state.data.system.safe_mode) }).catch((error) => alert(error.message)));
$("#monitor-toggle").addEventListener("click", () => mutation(state.data.system.monitoring_paused ? "/api/monitor/resume" : "/api/monitor/pause").catch((error) => alert(error.message)));
$("#logout").addEventListener("click", async () => { await api("/api/logout", { method: "POST", body: "{}" }); window.location.assign("/"); });
$("#export-data").addEventListener("click", () => window.location.assign("/api/export"));

$("#close-structure").addEventListener("click", async () => {
  try {
    const preview = await api("/api/close-previews", { method: "POST", body: JSON.stringify({ quantity: state.data.position.quantity_remaining }) });
    state.preview = preview;
    $("#preview-title").textContent = `${preview.structure_name} · ${preview.quantity} structure(s)`;
    $("#preview-economics").innerHTML = [["CURRENT MARKET VALUE", amount(preview.market_value)], ["EXPECTED PROCEEDS", amount(preview.liquidation_value)], ["ESTIMATED PNL", money(preview.estimated_pnl)], ["ESTIMATED RETURN", percent(preview.estimated_return)], ["ENGINE", preview.engine_action], ["DATA", `${preview.quote_provider} · ${age(preview.quote_timestamp)}`]].map(([label, value]) => `<div><span>${h(label)}</span><strong>${h(value)}</strong></div>`).join("");
    $("#preview-legs").innerHTML = preview.legs.map((leg) => `<div class="preview-leg"><strong>${h(leg.action)}</strong><span>${h(leg.quantity)} × ${h(leg.option_right)} ${h(leg.strike)} · ${h(leg.expiration.slice(0, 10))}<br><small>${h(leg.contract_identity)}</small></span></div>`).join("");
    $("#close-dialog").showModal();
  } catch (error) { alert(error.message); }
});
$("#preview-cancel").addEventListener("click", () => $("#close-dialog").close());
async function acknowledge() {
  try {
    const previewId = state.preview?.preview_id;
    if (!previewId) throw new Error("CLOSE_PREVIEW_CONTEXT_LOST — reopen the close preview.");
    await mutation(`/api/close-previews/${encodeURIComponent(previewId)}/acknowledge`);
    $("#close-dialog").close();
    alert("CLOSE_PREVIEW_READY — Close this entire combo manually in IBKR. Nothing was transmitted.");
  } catch (error) {
    if (error.message === "SENSITIVE_REAUTH_REQUIRED") { $("#close-dialog").close(); $("#reauth-dialog").showModal(); }
    else alert(error.message);
  }
}
$("#preview-ack").addEventListener("click", acknowledge);
$("#reauth-cancel").addEventListener("click", () => $("#reauth-dialog").close());
$("#reauth-submit").addEventListener("click", async () => {
  try { await mutation("/api/reauth", { password: $("#reauth-password").value }); $("#reauth-dialog").close(); await acknowledge(); }
  catch (error) { $("#reauth-error").textContent = error.message; }
});
$("#manual-close-reported").addEventListener("click", async () => {
  try { await mutation(`/api/close-previews/${encodeURIComponent(state.preview.preview_id)}/manual-close-reported`); $("#fill-dialog").showModal(); }
  catch (error) { alert(error.message); }
});
$("#fill-cancel").addEventListener("click", () => $("#fill-dialog").close());
$("#fill-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = new FormData(event.target); const value = (name) => Number(form.get(name));
  try {
    const result = await mutation(`/api/close-previews/${encodeURIComponent(state.preview.preview_id)}/reconcile`, {
      timestamp: new Date(String(form.get("timestamp"))).toISOString(), combo_fill_price: value("combo_fill_price"),
      quantity_closed: value("quantity_closed"), actual_fx_rate: form.get("actual_fx_rate") ? value("actual_fx_rate") : undefined,
      commission: value("commission"), fx_cost: value("fx_cost"), broker_reference: String(form.get("broker_reference") || "") || undefined,
    });
    $("#fill-dialog").close(); alert(`ACTUAL REALIZED PNL ${money(result.actual_realized_pnl)} · ESTIMATE ERROR ${money(result.estimate_error)}`);
  } catch (error) { $("#fill-error").textContent = error.message; }
});
document.querySelectorAll("[data-range]").forEach((button) => button.addEventListener("click", () => { state.range = button.dataset.range; renderChart(state.data.pnl_history); }));

refresh();
async function poll() {
  if (document.visibilityState === "visible") await refresh();
  const delay = state.data?.system?.conservation_mode ? 30_000 : document.visibilityState === "visible" ? 10_000 : 60_000;
  setTimeout(poll, delay);
}
setTimeout(poll, 10_000);
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") refresh(); });
