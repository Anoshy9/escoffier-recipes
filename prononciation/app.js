// Interface : leçons, écoute du modèle britannique, reconnaissance vocale et retour détaillé.

const $ = id => document.getElementById(id);
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

// ---------- Stockage local ----------
function load(key, fallback) {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* stockage indisponible */ }
}
const progress = load("pron.progress", {});
let custom = load("pron.custom", []);
const itemKey = item => item.en.toLowerCase().trim();

function record(item, score) {
  const k = itemKey(item);
  const p = progress[k] || { best: 0, n: 0 };
  p.best = Math.max(p.best, score);
  p.last = score;
  p.n++;
  progress[k] = p;
  save("pron.progress", progress);
  const today = new Date().toISOString().slice(0, 10);
  const day = load("pron.day", { date: today, n: 0 });
  if (day.date !== today) { day.date = today; day.n = 0; }
  day.n++;
  save("pron.day", day);
  renderStreak();
}

function renderStreak() {
  const today = new Date().toISOString().slice(0, 10);
  const day = load("pron.day", { date: today, n: 0 });
  $("streak").textContent = day.date === today && day.n ? day.n + " essai" + (day.n > 1 ? "s" : "") + " aujourd'hui" : "";
}

// ---------- Voix britannique ----------
let ukVoice = null;
function pickVoice() {
  if (!("speechSynthesis" in window)) return;
  const voices = speechSynthesis.getVoices();
  const gb = voices.filter(v => /en[-_]GB/i.test(v.lang));
  ukVoice = gb.find(v => /google/i.test(v.name)) || gb.find(v => v.localService) || gb[0] || null;
}
if ("speechSynthesis" in window) {
  pickVoice();
  speechSynthesis.onvoiceschanged = pickVoice;
}
function speak(text, rate = 0.95) {
  if (!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-GB";
  if (ukVoice) u.voice = ukVoice;
  u.rate = rate;
  speechSynthesis.speak(u);
}

// ---------- Navigation ----------
let deck = null;
let pos = 0;

function showHome() {
  stopListening();
  deck = null;
  $("view-home").hidden = false;
  $("view-practice").hidden = true;
  $("back").hidden = true;
  $("bar-title").textContent = "Say It British";
  renderHome();
  window.scrollTo(0, 0);
}

function openDeck(d, start = 0) {
  deck = d;
  pos = start;
  $("view-home").hidden = true;
  $("view-practice").hidden = false;
  $("back").hidden = false;
  $("bar-title").textContent = d.title;
  const tip = TIPS[d.tip];
  $("tip-box").hidden = !tip;
  if (tip) {
    $("tip-title").textContent = tip.title;
    $("tip-text").textContent = tip.text;
    $("tip-box").open = !progress[itemKey(d.items[0])];
  }
  history.pushState({ practice: true }, "");
  renderItem();
}

window.addEventListener("popstate", () => { if (deck) showHome(); });
$("back").addEventListener("click", () => history.back());

// ---------- Accueil ----------
function lessonScore(items) {
  const done = items.filter(i => progress[itemKey(i)]);
  if (!done.length) return { pct: 0, done: 0 };
  const sum = items.reduce((s, i) => s + (progress[itemKey(i)] ? progress[itemKey(i)].best : 0), 0);
  return { pct: Math.round(sum / items.length), done: done.length };
}

function lessonButton(sym, name, meta, pct, onClick) {
  const b = document.createElement("button");
  b.className = "lesson";
  b.innerHTML = (sym !== null ? '<span class="sym"></span>' : "") +
    '<span class="name"><span class="t"></span><span class="meta"></span></span>' +
    '<span class="progress" aria-hidden="true"><i></i></span>';
  if (sym !== null) sym.split(" ").forEach(part => {
    const span = document.createElement("span");
    span.textContent = part;
    b.querySelector(".sym").append(span, " ");
  });
  b.querySelector(".t").textContent = name;
  b.querySelector(".meta").textContent = meta;
  b.querySelector("i").style.width = pct + "%";
  b.addEventListener("click", onClick);
  return b;
}

function reviewItems() {
  const all = LESSONS.flatMap(l => l.items.map(i => ({ ...i, tip: l.tip })))
    .concat(custom.map(en => ({ en, ipa: "" })));
  return all.filter(i => progress[itemKey(i)] && progress[itemKey(i)].best < 70);
}

function renderHome() {
  const list = $("lesson-list");
  list.innerHTML = "";
  LESSONS.forEach(l => {
    const s = lessonScore(l.items);
    const meta = s.done ? `${s.done}/${l.items.length} essayés · ${s.pct} %` : `${l.items.length} exercices · ex. «\u00a0${l.sample}\u00a0»`;
    const li = document.createElement("li");
    li.appendChild(lessonButton(l.sound, l.title, meta, s.pct, () => openDeck({ title: l.title, tip: l.tip, items: l.items })));
    list.appendChild(li);
  });

  const cl = $("custom-list");
  cl.innerHTML = "";
  custom.forEach((en, idx) => {
    const p = progress[en.toLowerCase().trim()];
    const li = document.createElement("li");
    li.appendChild(lessonButton(null, en, p ? `Meilleur score : ${p.best} %` : "Pas encore essayée", p ? p.best : 0,
      () => openDeck({ title: "Ma phrase", tip: null, items: custom.map(e => ({ en: e, ipa: "" })) }, idx)));
    const del = document.createElement("button");
    del.className = "del";
    del.setAttribute("aria-label", "Supprimer cette phrase");
    del.textContent = "×";
    del.addEventListener("click", () => { custom.splice(idx, 1); save("pron.custom", custom); renderHome(); });
    li.appendChild(del);
    cl.appendChild(li);
  });

  const rev = reviewItems();
  $("review-card").hidden = !rev.length;
  $("review-count").textContent = rev.length + (rev.length > 1 ? " phrases sous 70 %" : " phrase sous 70 %");
}

$("review-go").addEventListener("click", () => {
  const items = reviewItems();
  if (items.length) openDeck({ title: "Révision", tip: null, items });
});

$("free-form").addEventListener("submit", e => {
  e.preventDefault();
  const text = $("free-text").value.trim().replace(/\s+/g, " ");
  if (!text) { $("free-text").focus(); return; }
  if (!custom.includes(text)) { custom.unshift(text); custom = custom.slice(0, 30); save("pron.custom", custom); }
  $("free-text").value = "";
  openDeck({ title: "Ma phrase", tip: null, items: [{ en: text, ipa: "" }] });
});

// ---------- Exercice ----------
function currentItem() { return deck.items[pos]; }

function renderItem() {
  stopListening();
  const item = currentItem();
  const target = $("target");
  target.innerHTML = "";
  item.en.split(" ").forEach((w, i) => {
    if (i) target.appendChild(document.createTextNode(" "));
    const s = document.createElement("span");
    s.className = "w";
    s.textContent = w;
    s.title = "Écouter ce mot";
    s.addEventListener("click", () => speak(w.replace(/[^A-Za-z']/g, ""), 0.7));
    target.appendChild(s);
  });
  $("ipa").textContent = item.ipa || "";
  $("item-pos").textContent = `${pos + 1} / ${deck.items.length}`;
  const p = progress[itemKey(item)];
  $("item-best").textContent = p ? `Meilleur : ${p.best} %` : "";
  $("result").hidden = true;
  $("interim").textContent = "";
  $("mic-status").textContent = SR ? "Touchez le micro et lisez la phrase" : "Reconnaissance vocale indisponible";
  $("prev").disabled = pos === 0;
  $("next").textContent = pos === deck.items.length - 1 ? "Terminer" : "Suivant →";
  resetRecording();
}

// Si on ne sait pas quel son corriger dans une phrase libre, on garde le conseil de la leçon.
function tipFor(issue) {
  const item = currentItem();
  if ((issue.tip === "generic" || issue.tip === "vowel") && (item.tip || deck.tip)) return item.tip || deck.tip;
  return issue.tip;
}

function showResult(heardTop, alternatives) {
  const item = currentItem();
  const r = analyse(item.en, heardTop);
  record(item, r.score);

  const score = $("score");
  score.textContent = r.score;
  score.className = "score " + (r.score >= 85 ? "good" : r.score >= 55 ? "warn" : "bad");
  $("verdict").textContent = r.score === 100 ? "Parfaitement compris !" :
    r.score >= 85 ? "Très bien compris" : r.score >= 55 ? "Compris en partie" : "Difficile à comprendre";
  $("heard").textContent = heardTop || "(rien)";

  const words = $("words");
  words.innerHTML = "";
  r.display.forEach((w, i) => {
    const s = document.createElement("span");
    s.className = r.status[i];
    s.textContent = w;
    words.appendChild(s);
  });

  const fb = $("feedback");
  fb.innerHTML = "";
  const byTip = new Map();
  r.issues.forEach(is => {
    const key = tipFor(is);
    if (!byTip.has(key)) byTip.set(key, []);
    byTip.get(key).push(is);
  });
  byTip.forEach((issues, key) => {
    const tip = TIPS[key] || TIPS.generic;
    const box = document.createElement("div");
    box.className = "fb";
    const h = document.createElement("h3");
    h.textContent = tip.title;
    const pair = document.createElement("div");
    pair.className = "pair";
    pair.textContent = issues.map(i => i.heard ? `«\u00a0${i.word}\u00a0» compris «\u00a0${i.heard}\u00a0»` : `«\u00a0${i.word}\u00a0» non entendu`).join(" · ");
    const p = document.createElement("p");
    p.textContent = tip.text;
    const row = document.createElement("div");
    row.className = "listen-row";
    row.style.justifyContent = "flex-start";
    row.style.marginTop = "8px";
    [...new Set(issues.map(i => i.word))].slice(0, 3).forEach(w => {
      const b = document.createElement("button");
      b.className = "btn ghost";
      b.textContent = "▶ " + w;
      b.addEventListener("click", () => speak(w, 0.7));
      row.appendChild(b);
    });
    box.append(h, pair, p, row);
    fb.appendChild(box);
  });

  const others = alternatives.filter(a => a && a.toLowerCase() !== (heardTop || "").toLowerCase());
  const nearly = r.score < 100 && others.some(a => analyse(item.en, a).score === 100);
  $("alts").textContent = nearly
    ? "Presque : la bonne phrase faisait partie des hypothèses de la reconnaissance. Articulez un peu plus nettement."
    : others.length ? "Autres interprétations possibles : " + others.slice(0, 3).map(a => `«\u00a0${a}\u00a0»`).join(", ") : "";

  $("result").hidden = false;
  $("item-best").textContent = `Meilleur : ${progress[itemKey(item)].best} %`;
  $("result").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "nearest" });
}

// ---------- Reconnaissance vocale ----------
let recognition = null;

function stopListening() {
  if (recognition) { recognition.onend = null; try { recognition.abort(); } catch (e) { /* déjà arrêtée */ } recognition = null; }
  $("mic").classList.remove("on");
}

// Dans une page intégrée (aperçu), le navigateur bloque le micro sans demander l'autorisation.
const EMBEDDED = (() => { try { return window.self !== window.top; } catch (e) { return true; } })();
const MIC_DENIED = EMBEDDED
  ? "Le micro est bloqué dans cet aperçu. Ouvrez l'application installée sur votre téléphone pour parler."
  : "Micro refusé. Autorisez le micro pour ce site dans les réglages de Chrome.";

const ERRORS = {
  "not-allowed": MIC_DENIED,
  "service-not-allowed": MIC_DENIED,
  "no-speech": "Je n'ai rien entendu. Touchez le micro puis parlez tout de suite.",
  "audio-capture": "Aucun micro trouvé, ou il est utilisé par une autre application.",
  "network": "La reconnaissance vocale a besoin d'internet. Vérifiez votre connexion."
};

function listen() {
  if (!SR) return;
  if (recognition) { recognition.stop(); return; }
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();

  const r = new SR();
  r.lang = "en-GB";
  r.interimResults = true;
  r.maxAlternatives = 5;
  r.continuous = false;
  let finals = [];
  let alternatives = [];
  let failed = false;

  r.onstart = () => {
    $("mic").classList.add("on");
    $("mic-status").textContent = "J'écoute… parlez maintenant";
    $("interim").textContent = "";
  };
  r.onresult = e => {
    let interim = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i];
      if (res.isFinal) {
        finals.push(res[0].transcript.trim());
        alternatives = Array.from(res).map(a => a.transcript.trim());
      } else {
        interim += res[0].transcript;
      }
    }
    $("interim").textContent = interim || finals.join(" ");
  };
  r.onerror = e => {
    failed = true;
    $("mic-status").textContent = ERRORS[e.error] || "La reconnaissance a échoué (" + e.error + "). Réessayez.";
  };
  r.onend = () => {
    recognition = null;
    $("mic").classList.remove("on");
    $("interim").textContent = "";
    if (finals.length) {
      $("mic-status").textContent = "Touchez le micro pour réessayer";
      const top = finals.join(" ");
      const prefix = finals.slice(0, -1).join(" ");
      showResult(top, alternatives.map(a => (prefix ? prefix + " " : "") + a));
    } else if (!failed) {
      $("mic-status").textContent = ERRORS["no-speech"];
    }
  };
  recognition = r;
  try { r.start(); } catch (e) { recognition = null; $("mic-status").textContent = "Impossible de démarrer le micro. Réessayez."; }
}

$("mic").addEventListener("click", listen);
$("play").addEventListener("click", () => speak(currentItem().en, 0.95));
$("play-slow").addEventListener("click", () => speak(currentItem().en, 0.6));
$("prev").addEventListener("click", () => { if (pos > 0) { pos--; renderItem(); } });
$("next").addEventListener("click", () => {
  if (pos < deck.items.length - 1) { pos++; renderItem(); window.scrollTo(0, 0); } else history.back();
});

// ---------- Enregistrement de sa propre voix ----------
let mediaRecorder = null;
let recordingUrl = null;
let recTimer = null;

function resetRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
  if (recordingUrl) URL.revokeObjectURL(recordingUrl);
  recordingUrl = null;
  $("rec-play").disabled = true;
  $("rec").textContent = "● M'enregistrer";
}

async function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") { mediaRecorder.stop(); return; }
  if (!navigator.mediaDevices || !window.MediaRecorder) {
    $("rec").textContent = "Enregistrement indisponible";
    $("rec").disabled = true;
    return;
  }
  stopListening();
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    $("mic-status").textContent = MIC_DENIED;
    return;
  }
  const chunks = [];
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
  mediaRecorder.onstop = () => {
    clearTimeout(recTimer);
    stream.getTracks().forEach(t => t.stop());
    if (recordingUrl) URL.revokeObjectURL(recordingUrl);
    recordingUrl = URL.createObjectURL(new Blob(chunks, { type: mediaRecorder.mimeType }));
    $("rec-play").disabled = false;
    $("rec").textContent = "● Recommencer";
  };
  mediaRecorder.start();
  $("rec").textContent = "■ Arrêter";
  recTimer = setTimeout(() => { if (mediaRecorder.state === "recording") mediaRecorder.stop(); }, 10000);
}

$("rec").addEventListener("click", toggleRecording);
$("rec-play").addEventListener("click", () => { if (recordingUrl) new Audio(recordingUrl).play(); });

// ---------- Démarrage ----------
if (!SR) $("unsupported").hidden = false;
renderStreak();
renderHome();

if ("serviceWorker" in navigator && location.protocol === "https:") {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}
