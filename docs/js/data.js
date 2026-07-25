import { PACKAGES_URL } from "./config.js";

export async function fetchPackages() {
  const res = await fetch(PACKAGES_URL, { cache: "no-store" });
  if (!res.ok) throw new Error(`${PACKAGES_URL}: ${res.status}`);
  return res.json();
}
