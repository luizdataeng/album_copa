const API_BASE = "";
const STORAGE_KEY = "album-cache-v1";
const HOLD_MS = 450;

const state = {
  selections: [],
  view: "home",
  filter: "Todas",
  current: null,
};

const appEl = document.getElementById("app");
const filterBar = document.getElementById("filters");
const modalEl = document.getElementById("modal");
const modalInput = document.getElementById("modal-input");

function getGroup(selection) {
  return selection.group || "Sem grupo";
}

function formatGroupLabel(group) {
  return group === "Sem grupo" ? "Sem grupo" : `Grupo ${group}`;
}

function getFlagPath(selection) {
  const name = (selection?.name || "").toLowerCase();
  if (name.includes("[mex]") || name.includes("mexico") || name.includes("mexixo")) {
    return "/static/flags/mexico.png";
  }
  if (name.includes("[bra]") || name.includes("brazil") || name.includes("brasil")) {
    return "/static/flags/brasil.png";
  }
  if (name.includes("[cze]") || name.includes("czechia")) {
    return "/static/flags/czechia.png";
  }
  if (name.includes("[kor]") || name.includes("korea")) {
    return "/static/flags/korea.png";
  }
  if (name.includes("[rsa]") || name.includes("south africa")) {
    return "/static/flags/south_africa.png";
  }
  if (name.includes("[can]") || name.includes("canada")) {
    return "/static/flags/canada.png";
  }
  if (name.includes("[bih]") || name.includes("bosnia")) {
    return "/static/flags/bosnia.png";
  }
  if (name.includes("[qat]") || name.includes("qatar")) {
    return "/static/flags/qatar.png";
  }
  if (name.includes("[sui]") || name.includes("switzerland")) {
    return "/static/flags/switzerland.png";
  }
  if (name.includes("[mar]") || name.includes("morocco")) {
    return "/static/flags/morocco.png";
  }
  if (name.includes("[hai]") || name.includes("haiti")) {
    return "/static/flags/haiti.png";
  }
  if (name.includes("[sco]") || name.includes("scotland")) {
    return "/static/flags/scotland.png";
  }
  if (name.includes("[usa]") || name.includes("usa") || name.includes("united states")) {
    return "/static/flags/usa.png";
  }
  if (name.includes("[par]") || name.includes("paraguay")) {
    return "/static/flags/paraguay.png";
  }
  if (name.includes("[aus]") || name.includes("australia")) {
    return "/static/flags/australia.png";
  }
  if (name.includes("[tur]") || name.includes("turkey")) {
    return "/static/flags/turkey.png";
  }
  if (name.includes("[cuw]") || name.includes("curacao") || name.includes("curaçao")) {
    return "/static/flags/curacao.png";
  }
  if (name.includes("[civ]") || name.includes("cote") || name.includes("côte")) {
    return "/static/flags/cote.png";
  }
  if (name.includes("[ecu]") || name.includes("ecuador")) {
    return "/static/flags/ecuador.png";
  }
  if (name.includes("[ger]") || name.includes("germany")) {
    return "/static/flags/germany.png";
  }
  if (name.includes("[jpn]") || name.includes("japan")) {
    return "/static/flags/japan.png";
  }
  if (name.includes("[ned]") || name.includes("netherlands")) {
    return "/static/flags/netherlands.png";
  }
  if (name.includes("[swe]") || name.includes("sweden")) {
    return "/static/flags/sweden.png";
  }
  if (name.includes("[tun]") || name.includes("tunisia")) {
    return "/static/flags/tunisia.png";
  }
  return "/static/flags/placeholder.png";
}

function cacheAlbum() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.selections));
}

function loadCachedAlbum() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (error) {
    return null;
  }
}

async function fetchAlbum() {
  try {
    const response = await fetch(`${API_BASE}/album`);
    if (!response.ok) throw new Error("Failed to fetch");
    const data = await response.json();
    state.selections = data.selections || [];
    cacheAlbum();
  } catch (error) {
    const cached = loadCachedAlbum();
    if (cached) state.selections = cached;
  }
  renderFilters();
  render();
}

async function updateSticker(selecao, number, delta) {
  const selection = state.selections.find((item) => item.name === selecao);
  if (!selection) return;
  const sticker = selection.stickers.find((item) => item.number === number);
  if (!sticker) return;

  const previous = sticker.quantity;
  sticker.quantity = Math.max(0, sticker.quantity + delta);
  render();

  try {
    const response = await fetch(`${API_BASE}/atualizar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selecao, numero: number, delta }),
    });
    if (!response.ok) throw new Error("Update failed");
    const payload = await response.json();
    sticker.quantity = payload.quantity;
    cacheAlbum();
  } catch (error) {
    sticker.quantity = previous;
    render();
  }
}

async function createSelection(name) {
  if (!name) return;
  try {
    const response = await fetch(`${API_BASE}/selecoes/nova`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) throw new Error("Create failed");
    await fetchAlbum();
  } catch (error) {
    console.warn(error);
  }
}

function ownedCount(selection) {
  return selection.stickers.filter((item) => item.quantity > 0).length;
}

function filterByGroup(selections) {
  if (state.filter === "Todas") return selections;
  return selections.filter((selection) => getGroup(selection) === state.filter);
}

function missingList() {
  return state.selections.map((selection) => ({
    name: selection.name,
    missing: selection.stickers.filter((item) => item.quantity === 0),
  }));
}

function repeatedList() {
  return state.selections.map((selection) => ({
    name: selection.name,
    repeated: selection.stickers.filter((item) => item.quantity >= 2),
  }));
}

function renderHome() {
  const filtered = filterByGroup(state.selections);

  const grouped = {};
  filtered.forEach((selection) => {
    const group = getGroup(selection);
    if (!grouped[group]) {
      grouped[group] = [];
    }
    grouped[group].push(selection);
  });

  const groupSections = Object.keys(grouped)
    .sort()
    .map((group) => {
      const cards = grouped[group]
        .map((selection) => {
          const progress = `${ownedCount(selection)}/${selection.stickers.length}`;
          return `
            <div class="selection-item">
              <div class="selection-title">${selection.name}</div>
              <div class="selection-progress">${progress}</div>
              <button class="card selection-flag-card" data-selection="${selection.name}">
                <img class="selection-flag" src="${getFlagPath(selection)}" alt="" />
              </button>
            </div>
          `;
        })
        .join("");

      return `
        <section class="group-section">
          <h2 class="group-heading">${formatGroupLabel(group)}</h2>
          <div class="group-grid">
            ${cards}
          </div>
        </section>
      `;
    })
    .join("");

  const emptyState =
    Object.keys(grouped).length === 0
      ? `<section class="group-section"><div class="card">Nenhuma selecao encontrada.</div></section>`
      : "";

  appEl.innerHTML = `
    <section>
      ${groupSections}
      ${emptyState}
      <div class="add-selection-wrapper">
        <button class="card text-left" id="add-selection">
          <div class="text-2xl font-semibold">+ Nova Selecao</div>
          <p class="text-sm text-slate-600">Criar um bloco personalizado.</p>
        </button>
      </div>
    </section>
  `;

  document.querySelectorAll("[data-selection]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.current = btn.dataset.selection;
      state.view = "selection";
      render();
    });
  });

  document.getElementById("add-selection").addEventListener("click", () => {
    modalEl.classList.remove("hidden");
    modalInput.value = "";
    modalInput.focus();
  });
}

function renderSelection() {
  const selection = state.selections.find((item) => item.name === state.current);
  if (!selection) {
    state.view = "home";
    render();
    return;
  }

  const stickerHtml = selection.stickers
    .map((sticker) => {
      const classes = ["sticker"];
      if (sticker.quantity >= 2) classes.push("repeated");
      else if (sticker.quantity === 1) classes.push("owned");

      const badge =
        sticker.quantity >= 2
          ? `<span class="badge">+${sticker.quantity - 1}</span>`
          : "";

      return `
        <button class="${classes.join(" ")}" data-number="${sticker.number}">
          ${badge}
          <span>${String(sticker.number).padStart(2, "0")}</span>
        </button>
      `;
    })
    .join("");

  appEl.innerHTML = `
    <section class="card">
      <div class="flex items-center selection-header">
        <div>
          <p class="text-sm uppercase tracking-[0.3em] text-slate-500">Selecao</p>
          <h2 class="text-2xl font-semibold">${selection.name}</h2>
        </div>
        <img class="selection-flag-detail" src="${getFlagPath(selection)}" alt="" />
        <button class="btn-ghost" id="back-home">Voltar</button>
      </div>
      <div class="mt-6 sticker-grid">
        ${stickerHtml}
      </div>
      <p class="mt-4 text-sm text-slate-600">
        Toque rapido soma 1. Toque longo remove 1.
      </p>
    </section>
  `;

  document.getElementById("back-home").addEventListener("click", () => {
    state.view = "home";
    render();
  });

  document.querySelectorAll("[data-number]").forEach((button) => {
    let holdTimer = null;
    let didHold = false;

    const onHold = () => {
      didHold = true;
      updateSticker(selection.name, Number(button.dataset.number), -1);
    };

    button.addEventListener("pointerdown", () => {
      didHold = false;
      holdTimer = setTimeout(onHold, HOLD_MS);
    });

    const release = () => {
      if (holdTimer) clearTimeout(holdTimer);
      if (!didHold) {
        updateSticker(selection.name, Number(button.dataset.number), 1);
      }
      holdTimer = null;
    };

    button.addEventListener("pointerup", release);
    button.addEventListener("pointerleave", () => {
      if (holdTimer) clearTimeout(holdTimer);
    });
    button.addEventListener("pointercancel", () => {
      if (holdTimer) clearTimeout(holdTimer);
    });
  });
}

function renderListView(type) {
  const baseSelections = filterByGroup(state.selections);
  const groups =
    type === "missing"
      ? baseSelections.map((selection) => ({
          name: selection.name,
          missing: selection.stickers.filter((item) => item.quantity === 0),
        }))
      : baseSelections.map((selection) => ({
          name: selection.name,
          repeated: selection.stickers.filter((item) => item.quantity >= 2),
        }));
  const title = type === "missing" ? "Faltam" : "Repetidas";

  const content = groups
    .map((group) => {
      const items = type === "missing" ? group.missing : group.repeated;
      if (items.length === 0) return "";

      const selection = baseSelections.find((item) => item.name === group.name);
      const flagPath = selection ? getFlagPath(selection) : getFlagPath({ name: group.name });

      const chips = items
        .map((item) => `<span class="chip">${item.number}</span>`)
        .join("");

      return `
        <div class="card list-card">
          <div class="list-card-header">
            <h3 class="text-lg font-semibold">${group.name}</h3>
            <img class="list-flag" src="${flagPath}" alt="" />
          </div>
          <div class="mt-3 flex flex-wrap gap-2">${chips}</div>
        </div>
      `;
    })
    .join("");

  appEl.innerHTML = `
    <section>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-semibold">${title}</h2>
        <button class="btn-ghost" id="back-home">Voltar</button>
      </div>
      <div class="grid">
        ${content || `<div class="card">Nada por aqui.</div>`}
      </div>
    </section>
  `;

  document.getElementById("back-home").addEventListener("click", () => {
    state.view = "home";
    render();
  });
}

function render() {
  const showFilters = state.view !== "selection";
  filterBar.classList.toggle("hidden", !showFilters);
  if (showFilters) {
    renderFilters();
  }

  if (state.view === "selection") {
    renderSelection();
    return;
  }

  if (state.view === "missing") {
    renderListView("missing");
    return;
  }

  if (state.view === "repeated") {
    renderListView("repeated");
    return;
  }

  renderHome();
}

function renderFilters() {
  const groups = Array.from(
    new Set(state.selections.map((selection) => getGroup(selection)))
  ).sort();
  const options = ["Todas", ...groups];

  if (!options.includes(state.filter)) {
    state.filter = "Todas";
  }

  filterBar.innerHTML = options
    .map(
      (option) =>
        `<button class="filter" data-filter="${option}">${
          option === "Todas" ? "Todas" : formatGroupLabel(option)
        }</button>`
    )
    .join("");

  document.querySelectorAll("[data-filter]").forEach((button) => {
    if (button.dataset.filter === state.filter) {
      button.classList.add("active");
    }
    button.addEventListener("click", () => {
      state.filter = button.dataset.filter;
      renderFilters();
      render();
    });
  });
}

function wireEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      render();
    });
  });

  document.getElementById("modal-cancel").addEventListener("click", () => {
    modalEl.classList.add("hidden");
  });

  document.getElementById("modal-save").addEventListener("click", () => {
    const name = modalInput.value.trim();
    modalEl.classList.add("hidden");
    createSelection(name);
  });

  modalEl.addEventListener("click", (event) => {
    if (event.target === modalEl) {
      modalEl.classList.add("hidden");
    }
  });

  if (navigator.serviceWorker) {
    navigator.serviceWorker.register("/sw.js");
  }
}

wireEvents();
fetchAlbum();
