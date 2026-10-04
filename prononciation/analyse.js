// Analyse : compare la phrase visée à ce que la reconnaissance vocale a compris,
// mot par mot, et devine quel son a posé problème.

const CONTRACTIONS = {
  "i'm": "i am", "you're": "you are", "we're": "we are", "they're": "they are", "it's": "it is",
  "that's": "that is", "what's": "what is", "where's": "where is", "there's": "there is",
  "he's": "he is", "she's": "she is", "let's": "let us", "don't": "do not", "doesn't": "does not",
  "didn't": "did not", "can't": "can not", "cannot": "can not", "won't": "will not",
  "isn't": "is not", "aren't": "are not", "wasn't": "was not", "couldn't": "could not",
  "wouldn't": "would not", "shouldn't": "should not", "i'd": "i would", "you'd": "you would",
  "i'll": "i will", "you'll": "you will", "we'll": "we will", "i've": "i have", "we've": "we have"
};

const UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
  "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"];
const TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];

function numberToWords(n) {
  if (n < 20) return UNITS[n];
  if (n < 100) return TENS[Math.floor(n / 10)] + (n % 10 ? " " + UNITS[n % 10] : "");
  if (n < 1000) return UNITS[Math.floor(n / 100)] + " hundred" + (n % 100 ? " and " + numberToWords(n % 100) : "");
  if (n < 10000) return UNITS[Math.floor(n / 1000)] + " thousand" + (n % 1000 ? " " + numberToWords(n % 1000) : "");
  return String(n);
}

const HOMOPHONE_KEY = new Map();
HOMOPHONES.forEach(group => group.forEach(w => HOMOPHONE_KEY.set(w, group[0])));

// Découpe une phrase en mots affichables ; chaque mot donne un ou plusieurs jetons normalisés.
function tokenize(text) {
  const words = text.replace(/[’‘]/g, "'").replace(/(\d),(\d)/g, "$1$2").split(/\s+/).filter(Boolean);
  const display = [];
  const tokens = [];
  words.forEach(raw => {
    const clean = raw.toLowerCase().replace(/[^a-z0-9']+/g, "").replace(/^'+|'+$/g, "");
    if (!clean) return;
    let parts;
    if (/^\d+$/.test(clean)) parts = numberToWords(parseInt(clean, 10)).split(" ");
    else if (CONTRACTIONS[clean]) parts = CONTRACTIONS[clean].split(" ");
    else parts = [clean];
    const idx = display.length;
    display.push(raw);
    parts.forEach(p => tokens.push({ word: p, key: HOMOPHONE_KEY.get(p) || p, display: idx }));
  });
  return { display, tokens };
}

// Alignement de Levenshtein mot à mot ; renvoie la liste des opérations.
function align(target, heard) {
  const n = target.length, m = heard.length;
  const d = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = 0; i <= n; i++) d[i][0] = i;
  for (let j = 0; j <= m; j++) d[0][j] = j;
  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      const same = target[i - 1].key === heard[j - 1].key;
      d[i][j] = Math.min(d[i - 1][j - 1] + (same ? 0 : 1), d[i - 1][j] + 1, d[i][j - 1] + 1);
    }
  }
  const ops = [];
  let i = n, j = m;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && d[i][j] === d[i - 1][j - 1] + (target[i - 1].key === heard[j - 1].key ? 0 : 1)) {
      ops.push({ type: target[i - 1].key === heard[j - 1].key ? "ok" : "sub", t: target[i - 1], h: heard[j - 1] });
      i--; j--;
    } else if (i > 0 && d[i][j] === d[i - 1][j] + 1) {
      ops.push({ type: "del", t: target[i - 1] });
      i--;
    } else {
      ops.push({ type: "ins", h: heard[j - 1] });
      j--;
    }
  }
  return ops.reverse();
}

const VOWELS = /[aeiouy]/;
const skeleton = w => w.replace(/[aeiouy]+/g, "_").replace(/(.)\1+/g, "$1");

// Devine le son en cause quand « t » a été compris comme « h ».
function diagnose(t, h) {
  if (!h) return "missing";
  for (const [a, b, tip] of MINIMAL_PAIRS) {
    if ((t === a && h === b) || (t === b && h === a)) return tip;
  }
  if (t.startsWith("h") && !h.startsWith("h") && (h === t.slice(1) || (VOWELS.test(h[0]) && skeleton(h) === skeleton(t.slice(1))))) return "h_drop";
  if (!t.startsWith("h") && h.startsWith("h") && (h.slice(1) === t || skeleton(h.slice(1)) === skeleton(t))) return "h_add";
  if (t.includes("th") && !h.includes("th")) {
    const fits = ["s", "z", "f", "v", "t", "d", ""].some(r => t.replace(/th/g, r) === h);
    if (fits || h.length >= t.length - 2) return VOICED_TH.has(t) ? "th_voiced" : "th_unvoiced";
  }
  if ((t[0] === "w" && h[0] === "v") || (t[0] === "v" && h[0] === "w")) return "w_v";
  if (t.endsWith("ed") && (h === t.slice(0, -2) || h === t.slice(0, -1) || h === t.slice(0, -3))) return "ed";
  if (t.endsWith("ing") && (h === t.slice(0, -3) + "in" || h === t.slice(0, -3))) return "ng";
  if (/[sdtzk]$/.test(t) && h === t.slice(0, -1)) return "final_s";
  if (h.length > 1 && t === h.slice(0, -1) && /[sdtz]$/.test(h)) return "final_s";
  if (/^r/.test(t) && /^[wl]/.test(h)) return "r";
  if (skeleton(t) === skeleton(h)) {
    if (/ee|ea|ie|ei/.test(t) || /ee|ea/.test(h)) return "ih_ee";
    if (/oo|u/.test(t) && /oo|u/.test(h)) return "uu";
    if (/oa|ow|ay|ai|ey|o[^aeiou]e$|a[^aeiou]e$/.test(t) || /^[^aeiou]*o$/.test(t)) return "diph";
    if (/a|u/.test(t)) return "a_vowels";
    return "vowel";
  }
  if (t.length >= 7) return "stress";
  return "generic";
}

// Analyse complète d'un essai.
function analyse(targetText, heardText) {
  const target = tokenize(targetText);
  const heard = tokenize(heardText || "");
  const ops = align(target.tokens, heard.tokens);
  const status = target.display.map(() => "ok");
  const issues = [];
  let okCount = 0;
  ops.forEach(op => {
    if (op.type === "ok") { okCount++; return; }
    if (op.type === "ins") return;
    status[op.t.display] = op.type === "del" ? "missing" : "wrong";
    const tip = op.type === "del" ? "missing" : diagnose(op.t.word, op.h.word);
    issues.push({ word: op.t.word, heard: op.h ? op.h.word : null, tip });
  });
  const extra = ops.filter(o => o.type === "ins").length;
  const total = target.tokens.length || 1;
  const score = Math.max(0, Math.round(100 * (okCount - 0.5 * extra) / total));
  return { display: target.display, status, issues, score: Math.min(100, score) };
}

if (typeof module !== "undefined") module.exports = { analyse, diagnose, tokenize, numberToWords };
