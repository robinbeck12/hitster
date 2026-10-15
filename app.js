// ZeitHit – Player, Auflösung und Hash-Routing.
// Zustände: bereit → karte geladen → spielt → aufgelöst → (nächste Karte)

const $ = (id) => document.getElementById(id);

const screens = {
  start: $("screen-start"),
  scanner: $("screen-scanner"),
  player: $("screen-player"),
};
const el = {
  btnScan: $("btn-scan"),
  btnScanCancel: $("btn-scan-cancel"),
  scanNotice: $("scan-notice"),
  scanHint: $("scan-hint"),
  reader: $("reader"),
  title: $("app-title"),
  startNotice: $("start-notice"),
  playerNotice: $("player-notice"),
  cardId: $("card-id"),
  overlayStage: $("stage"),
  revealHidden: $("reveal-hidden"),
  revealShown: $("reveal-shown"),
  year: $("reveal-year"),
  songTitle: $("reveal-title"),
  artist: $("reveal-artist"),
  btnPlay: $("btn-play"),
  btnBack: $("btn-back"),
  btnReveal: $("btn-reveal"),
  btnNext: $("btn-next"),
};

const MSG_OFFLINE = "Für die Musik wird Internet gebraucht.";
const MSG_UNKNOWN = "Diese Karte kenne ich nicht.";
const MSG_NO_VIDEO = "Für diese Karte ist noch kein Song eingetragen.";
const MSG_NOT_EMBEDDABLE = "Dieser Song lässt sich nicht einbetten. Bitte eine andere Karte wählen.";
const MSG_CAMERA_DENIED =
  "Kamerazugriff verweigert. Bitte in den iPhone-Einstellungen (Safari bzw. ZeitHit) die Kamera erlauben.";
const MSG_NO_CAMERA = "Keine Kamera gefunden.";
const MSG_CAMERA_FAILED = "Die Kamera konnte nicht gestartet werden.";
const YT_API_TIMEOUT_MS = 10000;
const SCANNER_LIB = "./vendor/html5-qrcode.min.js";

const DECADE_COLORS = [
  [2020, "--dec-20"],
  [2010, "--dec-10"],
  [2000, "--dec-00"],
  [1990, "--dec-90"],
  [1980, "--dec-80"],
  [1970, "--dec-70"],
  [0, "--dec-60"],
];

let config = { appName: "ZeitHit" };
let songs = [];
let current = null; // aktuell geladener Song
let player = null; // YT.Player
let loadToken = 0; // verwirft veraltete asynchrone Ladevorgänge
let wakeLock = null;

// ---------- Anzeige ----------

function showScreen(name) {
  for (const [key, node] of Object.entries(screens)) node.hidden = key !== name;
}

function setNotice(node, text) {
  node.textContent = text ?? "";
  node.hidden = !text;
}

function setPlaying(playing) {
  screens.player.classList.toggle("is-playing", playing);
  el.btnPlay.setAttribute("aria-label", playing ? "Pause" : "Abspielen");
  if (playing) requestWakeLock();
  else releaseWakeLock();
}

function decadeColor(year) {
  const [, variable] = DECADE_COLORS.find(([from]) => year >= from);
  return `var(${variable})`;
}

function setPlayerControls(enabled) {
  el.btnPlay.disabled = !enabled;
  el.btnBack.disabled = !enabled;
}

function resetReveal() {
  el.revealHidden.hidden = false;
  el.revealShown.hidden = true;
  el.btnReveal.disabled = false;
}

function reveal() {
  if (!current) return;
  el.year.textContent = String(current.year);
  el.year.style.setProperty("--year-color", decadeColor(current.year));
  el.songTitle.textContent = current.title;
  el.artist.textContent = current.artist;
  el.revealHidden.hidden = true;
  el.revealShown.hidden = false;
  el.btnReveal.disabled = true;
}

// ---------- Wake Lock (optional) ----------

async function requestWakeLock() {
  try {
    if ("wakeLock" in navigator && !wakeLock) {
      wakeLock = await navigator.wakeLock.request("screen");
      wakeLock.addEventListener("release", () => (wakeLock = null));
    }
  } catch {
    wakeLock = null;
  }
}

function releaseWakeLock() {
  wakeLock?.release().catch(() => {});
  wakeLock = null;
}

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && screens.player.classList.contains("is-playing")) {
    requestWakeLock();
  }
});

// ---------- YouTube ----------

function loadYouTubeApi() {
  if (window.YT?.Player) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    const timer = setTimeout(() => fail(), YT_API_TIMEOUT_MS);
    const fail = () => {
      clearTimeout(timer);
      script.remove();
      window.onYouTubeIframeAPIReady = undefined;
      reject(new Error("YouTube-API nicht erreichbar"));
    };
    window.onYouTubeIframeAPIReady = () => {
      clearTimeout(timer);
      resolve();
    };
    script.src = "https://www.youtube.com/iframe_api";
    script.onerror = fail;
    document.head.appendChild(script);
  });
}

function onPlayerStateChange(event) {
  const S = window.YT.PlayerState;
  if (event.data === S.PLAYING) setPlaying(true);
  else if (event.data === S.PAUSED || event.data === S.ENDED || event.data === S.CUED) setPlaying(false);
}

function onPlayerError() {
  setPlaying(false);
  setPlayerControls(false);
  setNotice(el.playerNotice, MSG_NOT_EMBEDDABLE);
}

function createPlayer(song) {
  return new Promise((resolve) => {
    player = new window.YT.Player("yt-player", {
      videoId: song.yt,
      playerVars: {
        controls: 0,
        modestbranding: 1,
        playsinline: 1,
        rel: 0,
        start: song.start ?? 0,
      },
      events: {
        onReady: () => resolve(),
        onStateChange: onPlayerStateChange,
        onError: onPlayerError,
      },
    });
  });
}

async function showSong(song) {
  const token = ++loadToken;
  stopScanner();
  current = song;
  setNotice(el.playerNotice, "");
  resetReveal();
  setPlaying(false);
  setPlayerControls(false);
  el.cardId.textContent = `Karte ${song.id}`;
  showScreen("player");

  try {
    await loadYouTubeApi();
    if (token !== loadToken) return;
    if (player) {
      player.cueVideoById({ videoId: song.yt, startSeconds: song.start ?? 0 });
    } else {
      await createPlayer(song);
      if (token !== loadToken) return;
    }
    setPlayerControls(true);
  } catch {
    if (token !== loadToken) return;
    setNotice(el.playerNotice, MSG_OFFLINE);
  }
}

function stopPlayback() {
  try {
    player?.stopVideo();
  } catch {
    /* Player evtl. noch nicht bereit */
  }
  setPlaying(false);
}

// ---------- Scanner ----------

let scanner = null; // Html5Qrcode-Instanz, solange die Kamera läuft
let scanHandled = false; // entprellt Doppelscans

function loadScannerLib() {
  if (window.Html5Qrcode) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = SCANNER_LIB;
    script.onload = () => resolve();
    script.onerror = () => {
      script.remove();
      reject(new Error("Scanner-Bibliothek fehlt"));
    };
    document.head.appendChild(script);
  });
}

function cameraErrorMessage(err) {
  const text = `${err?.name ?? ""} ${err?.message ?? err ?? ""}`;
  if (/NotAllowed|Permission|denied/i.test(text)) return MSG_CAMERA_DENIED;
  if (/NotFound|DevicesNotFound|no camera|not found/i.test(text)) return MSG_NO_CAMERA;
  return MSG_CAMERA_FAILED;
}

async function stopScanner() {
  const s = scanner;
  scanner = null;
  if (!s) return;
  try {
    if (s.isScanning) await s.stop();
    s.clear();
  } catch {
    /* Kamera war schon beendet */
  }
}

async function startScan() {
  loadToken++;
  stopPlayback();
  current = null;
  scanHandled = false;
  setNotice(el.scanNotice, "");
  el.scanHint.hidden = false;
  showScreen("scanner");
  const token = loadToken;

  try {
    await loadScannerLib();
    if (token !== loadToken) return;
    if (!navigator.mediaDevices?.getUserMedia) throw new Error("NotFound: keine Kamera-API");
    scanner = new window.Html5Qrcode("reader", { verbose: false });
    const instance = scanner;
    await instance.start(
      { facingMode: "environment" },
      {
        fps: 10,
        qrbox: (w, h) => {
          const edge = Math.floor(Math.min(w, h) * 0.7);
          return { width: edge, height: edge };
        },
      },
      (text) => {
        if (scanHandled) return;
        scanHandled = true;
        stopScanner().then(() => openScanned(text));
      },
      () => {} // Frames ohne QR-Code ignorieren
    );
    if (token !== loadToken) await stopScanner();
  } catch (err) {
    if (token !== loadToken) return;
    await stopScanner();
    el.scanHint.hidden = true;
    setNotice(el.scanNotice, cameraErrorMessage(err));
  }
}

// ---------- Karten laden / Routing ----------

function extractId(text) {
  return /(\d{3})$/.exec((text ?? "").trim())?.[1] ?? null;
}

function goToStart(message) {
  loadToken++;
  stopScanner();
  stopPlayback();
  current = null;
  setNotice(el.startNotice, message);
  showScreen("start");
}

function loadCard(id) {
  const song = songs.find((s) => s.id === id);
  if (!song) return goToStart(MSG_UNKNOWN);
  if (!song.yt || song.yt === "TODO") return goToStart(MSG_NO_VIDEO);
  setNotice(el.startNotice, "");
  showSong(song);
}

function route() {
  const id = extractId(location.hash.replace(/^#/, ""));
  if (id) loadCard(id);
  else if (!current) goToStart("");
}

/** Wird vom Scanner mit dem gelesenen Text aufgerufen: volle URL oder nur die ID. */
function openScanned(text) {
  const id = extractId(text);
  if (!id) return goToStart(MSG_UNKNOWN);
  if (location.hash === `#${id}`) loadCard(id);
  else location.hash = id;
}

// ---------- Bedienung ----------

el.btnPlay.addEventListener("click", () => {
  if (!player) return;
  // Muss direkt im Tipp-Handler laufen, sonst blockt iOS die Wiedergabe.
  if (screens.player.classList.contains("is-playing")) player.pauseVideo();
  else player.playVideo();
});

el.btnBack.addEventListener("click", () => {
  if (!player) return;
  player.seekTo(Math.max(0, player.getCurrentTime() - 10), true);
});

el.btnReveal.addEventListener("click", reveal);

el.btnScan.addEventListener("click", startScan);

el.btnScanCancel.addEventListener("click", () => goToStart(""));

el.btnNext.addEventListener("click", () => {
  history.replaceState(null, "", location.pathname + location.search);
  startScan();
});

window.addEventListener("hashchange", route);

// ---------- Start ----------

async function init() {
  try {
    const [cfg, list] = await Promise.all([
      fetch("./config.json").then((r) => r.json()),
      fetch("./songs.json").then((r) => r.json()),
    ]);
    config = cfg;
    songs = list;
  } catch {
    setNotice(el.startNotice, "Daten konnten nicht geladen werden.");
  }
  document.title = config.appName;
  el.title.textContent = config.appName;
  route();
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch(() => {});
}

init();
