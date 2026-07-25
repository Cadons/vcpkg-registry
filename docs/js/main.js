import { fetchPackages } from "./data.js";
import { renderGrid } from "./render.js";
import { initCopyButtons } from "./clipboard.js";
import { initSearch } from "./search.js";

async function main() {
  const grid = document.getElementById("grid");
  const empty = document.getElementById("empty");
  const count = document.getElementById("count");
  const search = document.getElementById("search");

  let packages = [];
  try {
    packages = await fetchPackages();
  } catch (e) {
    grid.innerHTML = `<div class="empty">Could not load packages.json.</div>`;
    return;
  }

  grid.innerHTML = renderGrid(packages);
  initCopyButtons(grid);
  initSearch({ input: search, grid, empty, count, total: packages.length });
}

main();
