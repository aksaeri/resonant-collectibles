(function () {
  const D = JSON.parse(document.getElementById("data").textContent);
  const cats = Object.fromEntries(D.categories.map(c => [c.id, c]));
  const FLAG = { "post-story": "After story", "game-plus": "Game+", unverified: "Unconfirmed" };
  const ZONE_LABEL = z => z === "Other" ? "No fixed location" : z;
  const LS = "rc-archive-found-v1", UI = "rc-archive-ui-v1", COLL = "archive";

  let found = new Set();
  let ui = { showAll: false, group: "cat", cat: "", zone: "", q: "" };
  let mode = "local";
  let canWrite = true;
  let dbRef = null;
  let pending = null;

  try { ui = Object.assign(ui, JSON.parse(localStorage.getItem(UI) || "{}"), { q: "" }); } catch (e) {}
  try { found = new Set(JSON.parse(localStorage.getItem(LS) || "[]")); } catch (e) {}

  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const saveUI = () => { try { localStorage.setItem(UI, JSON.stringify({ showAll: ui.showAll, group: ui.group, cat: ui.cat, zone: ui.zone })); } catch (e) {} };
  const saveLocal = () => { try { localStorage.setItem(LS, JSON.stringify([...found])); } catch (e) {} };
  const setSync = (text, warn) => { const s = $("sync"); s.textContent = text; s.classList.toggle("warn", !!warn); };

  $("f-cat").innerHTML = '<option value="">All categories</option>' + D.categories.map(c => '<option value="' + c.id + '">' + esc(c.name) + "</option>").join("");
  $("f-zone").innerHTML = '<option value="">All zones</option>' + D.zones.map(z => '<option value="' + esc(z) + '">' + esc(ZONE_LABEL(z)) + "</option>").join("");

  function renderHeader() {
    const n = D.items.filter(i => found.has(i.id)).length, t = D.items.length;
    $("tally").innerHTML = "<b>" + n + "</b><span> / " + t + "</span>";
    $("totalbar").style.width = (100 * n / t) + "%";
    $("show-missing").setAttribute("aria-pressed", !ui.showAll);
    $("show-all").setAttribute("aria-pressed", ui.showAll);
    $("group-zone").setAttribute("aria-pressed", ui.group === "zone");
    $("group-cat").setAttribute("aria-pressed", ui.group === "cat");
    $("f-cat").value = ui.cat; $("f-zone").value = ui.zone;
  }

  function itemRow(i) {
    const f = found.has(i.id);
    const sub = ui.group === "cat" ? ZONE_LABEL(i.zone) : cats[i.category].name + " " + i.n;
    const flags = i.flags.map(x => '<span class="req">' + esc(FLAG[x] || x) + "</span>").join("");
    const meta = [i.place && "Location: " + i.place, i.quest && "Quest: " + i.quest, i.unlocks && "Unlocks: " + i.unlocks]
      .filter(Boolean).map(x => "<span>" + esc(x) + "</span>").join("");
    return '<li class="item' + (f ? " found" : "") + '"><label>' +
      '<input type="checkbox" id="cb-' + i.id + '" data-id="' + i.id + '"' + (f ? " checked" : "") + (canWrite ? "" : " disabled") + ">" +
      '<span class="ihead"><span class="iname">' + (ui.group === "cat" ? '<span class="tag">' + String(i.n).padStart(2, "0") + "</span> " : "") + esc(i.title) +
      '</span><span class="tag">' + esc(sub) + "</span>" + flags + (f ? '<span class="stampbadge">FOUND</span>' : "") + "</span>" +
      (meta ? '<span class="meta">' + meta + "</span>" : "") +
      '<span class="loc">' + esc(i.how) + "</span></label></li>";
  }

  function renderList() {
    const q = ui.q.trim().toLowerCase();
    const visible = D.items.filter(i =>
      (ui.showAll || !found.has(i.id)) && (!ui.cat || i.category === ui.cat) && (!ui.zone || i.zone === ui.zone) &&
      (!q || (i.title + " " + i.place + " " + i.quest + " " + i.how + " " + cats[i.category].name).toLowerCase().includes(q)));

    const groups = ui.group === "cat"
      ? D.categories.map(c => ({ key: c.id, title: c.name, num: String(c.order).padStart(2, "0"), all: D.items.filter(i => i.category === c.id) }))
      : D.zones.map((z, n) => ({ key: z, title: ZONE_LABEL(z), num: String(n + 1).padStart(2, "0"), all: D.items.filter(i => i.zone === z) }));

    let html = "";
    for (const g of groups) {
      const rows = visible.filter(i => g.all.includes(i));
      if (!rows.length) continue;
      const f = g.all.filter(i => found.has(i.id)).length;
      const missing = g.all.length - f;
      let action = "";
      if (canWrite && missing > 0) {
        action = pending === g.key
          ? '<span class="confirm">Tick all ' + missing + '? <button type="button" data-confirm="' + esc(g.key) + '">Yes</button><button type="button" data-cancel="1">No</button></span>'
          : '<button type="button" class="linkbtn" data-tickall="' + esc(g.key) + '">tick all</button>';
      }
      html += '<section class="zone"><div class="zhead"><h2><em>' + g.num + "</em>" + esc(g.title) + "</h2>" +
        '<span class="zmeta"><span class="' + (missing ? "" : "clear") + '">' + f + "/" + g.all.length + "</span>" + action + "</span></div>" +
        '<ul class="items">' + rows.map(itemRow).join("") + "</ul></section>";
    }
    if (!html) {
      html = found.size >= D.items.length
        ? '<div class="empty"><strong>Archive complete</strong>All ' + D.items.length + " collectibles are ticked off.</div>"
        : '<div class="empty"><strong>Nothing missing here</strong>No missing items match these filters. Switch to All to see found items.</div>';
    }
    $("list").innerHTML = html;
  }

  function render() { renderHeader(); renderList(); }

  async function setFound(ids, value) {
    for (const id of ids) value ? found.add(id) : found.delete(id);
    saveLocal();
    render();
    if (mode !== "db") return;
    try {
      for (const id of ids) {
        const ref = dbRef.collection(COLL).doc(id);
        if (value) await ref.set({ found: true, at: new Date().toISOString() });
        else await ref.delete();
      }
    } catch (e) {
      if (e && e.code === "invalid_argument") { canWrite = false; setSync("Read only. You can't change this log.", true); render(); }
      else setSync("Couldn't save to your account. Saved on this device.", true);
    }
  }

  document.addEventListener("change", e => {
    const t = e.target;
    if (t.dataset && t.dataset.id) setFound([t.dataset.id], t.checked);
    else if (t.id === "f-cat") { ui.cat = t.value; saveUI(); render(); }
    else if (t.id === "f-zone") { ui.zone = t.value; saveUI(); render(); }
  });
  document.addEventListener("click", e => {
    const t = e.target.closest("button");
    if (!t) return;
    if (t.id === "show-missing" || t.id === "show-all") { ui.showAll = t.id === "show-all"; saveUI(); render(); }
    else if (t.id === "group-zone" || t.id === "group-cat") { ui.group = t.id === "group-zone" ? "zone" : "cat"; pending = null; saveUI(); render(); }
    else if (t.dataset.tickall) { pending = t.dataset.tickall; renderList(); }
    else if (t.dataset.cancel) { pending = null; renderList(); }
    else if (t.dataset.confirm) {
      const k = t.dataset.confirm; pending = null;
      const key = ui.group === "cat" ? "category" : "zone";
      setFound(D.items.filter(i => i[key] === k && !found.has(i.id)).map(i => i.id), true);
    }
  });
  $("q").addEventListener("input", e => { ui.q = e.target.value; renderList(); });

  render();

  (async function connect() {
    const db = window.claude && window.claude.use ? await window.claude.use("db") : null;
    if (!db) { setSync("Saved on this device only."); return; }
    const user = await window.claude.use("user");
    if (user && (await user.can("data.write")) === false) canWrite = false;
    dbRef = db;
    let first = true;
    db.collection(COLL).limit(1000).onSnapshot(snap => {
      const remote = new Set(snap.docs.filter(d => d.exists).map(d => d.id));
      if (first && remote.size === 0 && found.size > 0 && canWrite) {
        // First run with the account store: carry over ticks made on this device.
        first = false; mode = "db";
        setFound([...found], true);
        setSync("Synced to your account.");
        return;
      }
      first = false; mode = "db";
      found = remote; saveLocal(); render();
      setSync(canWrite ? "Synced to your account." : "Read only.");
    }, () => { mode = "local"; setSync("Sync stopped. Saving on this device.", true); });
  })();
})();
