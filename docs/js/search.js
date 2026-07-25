export function initSearch({ input, grid, empty, count, total }) {
  function applyFilter() {
    const q = input.value.trim().toLowerCase();
    const cards = grid.querySelectorAll(".card");
    let visible = 0;
    cards.forEach(card => {
      const match = !q || card.dataset.name.includes(q) || card.dataset.desc.includes(q);
      card.hidden = !match;
      if (match) visible++;
    });
    empty.hidden = visible !== 0;
    count.textContent = `${visible} of ${total} package${total === 1 ? "" : "s"}`;
  }

  input.addEventListener("input", applyFilter);
  applyFilter();
}
