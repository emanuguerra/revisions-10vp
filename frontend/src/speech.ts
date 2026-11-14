// Pronunciation with the browser's built-in voices (Web Speech API).
// `lang` is a BCP 47 tag: "en-GB" (default), "de-DE" for German units (speech_lang in unit.yaml),
// "fr-FR" for French words. A text is only ever read by a voice of its own language: a German
// word read by an English voice gets an English accent, so with no matching voice we say so.
//
// Voice choice, best first: the one picked by the student in the sound check (remembered in this
// browser), then the natural / online voices (Google, Microsoft Natural, Apple Premium), the exact
// country (de-DE before de-CH), then any voice of the language.

const PREF_KEY = (lang: string) => `voice:${prefix(lang)}`;
const GOOD = /google|natural|online|neural|premium|enhanced|siri/i;

const prefix = (lang: string) => lang.slice(0, 2).toLowerCase();
const tag = (l: string) => l.toLowerCase().replace("_", "-");

export const speechSupported = typeof window !== "undefined" && "speechSynthesis" in window;

function allVoices(): SpeechSynthesisVoice[] {
  try { return speechSynthesis.getVoices(); } catch { return []; }
}

/** Voices browsers load late (Chrome): wait for them, at most 1.5 s. */
let loading: Promise<void> | null = null;
function voicesReady(): Promise<void> {
  if (!speechSupported || allVoices().length) return Promise.resolve();
  loading ??= new Promise<void>(resolve => {
    const done = () => resolve();
    try { speechSynthesis.addEventListener("voiceschanged", done, { once: true }); } catch { /* old browsers */ }
    setTimeout(done, 1500);
  });
  return loading;
}
if (speechSupported) allVoices();  // starts loading the list in Chrome

function score(v: SpeechSynthesisVoice, lang: string): number {
  return (GOOD.test(v.name) ? 4 : 0) + (tag(v.lang) === tag(lang) ? 2 : 0) + (v.localService ? 0 : 1);
}

/** Voices of the language of `lang`, best first. */
export function voicesFor(lang = "en-GB"): SpeechSynthesisVoice[] {
  return allVoices().filter(v => tag(v.lang).startsWith(prefix(lang)))
    .sort((a, b) => score(b, lang) - score(a, lang));
}

export function preferredVoiceName(lang: string): string | null {
  try { return localStorage.getItem(PREF_KEY(lang)); } catch { return null; }
}

export function setPreferredVoice(lang: string, name: string | null) {
  try { name ? localStorage.setItem(PREF_KEY(lang), name) : localStorage.removeItem(PREF_KEY(lang)); } catch { /* private mode */ }
}

export function currentVoice(lang = "en-GB"): SpeechSynthesisVoice | null {
  const vs = voicesFor(lang);
  const pref = preferredVoiceName(lang);
  return vs.find(v => v.name === pref) ?? vs[0] ?? null;
}

/** Written-only marks a voice would read aloud: "content·e" → "content", "a / b" → "a, b". */
function forSpeech(text: string, lang: string): string {
  const t = text.replace(/\s\/\s/g, ", ");
  return prefix(lang) === "fr" ? t.replace(/·[a-zàâäçéèêëîïôöùûü]+/gi, "") : t;
}

export type SpeakResult = "ok" | "novoice" | "failed";

/** Reads `text` with a voice of `lang`. Resolves "novoice" if the browser has none for it. */
export async function say(text: string, lang = "en-GB"): Promise<SpeakResult> {
  if (!speechSupported) return "failed";
  await voicesReady();
  const voice = currentVoice(lang);
  if (!voice) return "novoice";
  return new Promise(resolve => {
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(forSpeech(text, lang));
      u.voice = voice;
      u.lang = voice.lang;
      u.rate = 0.9;
      let started = false;
      u.onstart = () => { started = true; resolve("ok"); };
      u.onerror = () => { if (!started) resolve("failed"); };
      // Chrome drops a speak() that follows cancel() too closely
      setTimeout(() => { try { speechSynthesis.resume(); speechSynthesis.speak(u); } catch { resolve("failed"); } }, 60);
      setTimeout(() => { if (!started) resolve("failed"); }, 2500);
    } catch { resolve("failed"); }
  });
}

/** Same as `say`, true if the audio started. */
export const speak = (text: string, lang = "en-GB") => say(text, lang).then(r => r === "ok");

const LANG_NAMES: Record<string, string> = { de: "allemande", en: "anglaise", fr: "française" };
export const langName = (lang: string) => LANG_NAMES[prefix(lang)] ?? lang;

/** Button label after an attempt to speak. */
export function sayLabel(r: SpeakResult, lang: string, idle: string): string {
  if (r === "ok") return idle;
  if (r === "novoice") return `🔇 Pas de voix ${langName(lang)} : essaie Google ↗`;
  return "🔇 Pas de son, essaie Google ↗";
}

export const translateLink = (w: string, lang = "en-GB") =>
  `https://translate.google.com/?sl=${prefix(lang)}&tl=${prefix(lang) === "fr" ? "de" : "fr"}&op=translate&text=${encodeURIComponent(w)}`;
