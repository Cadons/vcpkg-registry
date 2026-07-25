import { escapeHtml } from "./utils.js";
import { configSnippet, depsSnippet } from "./snippets.js";

function renderDeps(pkg) {
  if (!pkg.dependencies.length) return "";
  const chips = pkg.dependencies
    .map(d => `<span class="dep${d.host ? " host" : ""}" title="${d.host ? "host dependency" : "dependency"}">${escapeHtml(d.name)}</span>`)
    .join("");
  return `<div class="deps"><div class="deps-label">Dependencies</div><div class="dep-list">${chips}</div></div>`;
}

export function renderCard(pkg) {
  const versionLabel = pkg.port_version ? `${pkg.version}#${pkg.port_version}` : pkg.version;
  const homepage = pkg.homepage
    ? `<div class="homepage"><a href="${escapeHtml(pkg.homepage)}" target="_blank" rel="noopener">${escapeHtml(pkg.homepage)}</a></div>`
    : "";
  const license = pkg.license ? `<span class="badge">${escapeHtml(pkg.license)}</span>` : "";

  return `
  <article class="card" data-name="${escapeHtml(pkg.name.toLowerCase())}" data-desc="${escapeHtml(pkg.description.toLowerCase())}">
    <div class="card-head">
      <h2>${escapeHtml(pkg.name)}</h2>
      <div class="badges">
        <span class="badge">${escapeHtml(versionLabel)}</span>
        ${license}
      </div>
    </div>
    <p class="desc">${escapeHtml(pkg.description)}</p>
    ${homepage}
    ${renderDeps(pkg)}
    <details class="usage">
      <summary>How to use</summary>
      <div>
        <pre><code>${escapeHtml(configSnippet(pkg))}</code><button class="copy-btn" data-copy>Copy</button></pre>
        <pre><code>${escapeHtml(depsSnippet(pkg))}</code><button class="copy-btn" data-copy>Copy</button></pre>
      </div>
    </details>
  </article>`;
}

export function renderGrid(packages) {
  return packages.map(renderCard).join("");
}
