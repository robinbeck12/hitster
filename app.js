// ZeitHit – Einstiegspunkt (Player-Logik folgt in P3).
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch(() => {});
}
