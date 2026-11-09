// Pronunciation with the browser's built-in voices (Web Speech API).
// Works only if the browser has an English voice installed (Chrome and Edge on Windows do).

let voice: SpeechSynthesisVoice | null = null;

export function englishVoices(): SpeechSynthesisVoice[] {
  try { return speechSynthesis.getVoices().filter(v => /^en/i.test(v.lang)); } catch { return []; }
}

function pickVoice() {
  const vs = englishVoices();
  voice = vs.find(v => /en[-_]GB/i.test(v.lang)) ?? vs[0] ?? null;
}

export const speechSupported = typeof window !== "undefined" && "speechSynthesis" in window;
if (speechSupported) {
  pickVoice();
  try { speechSynthesis.addEventListener("voiceschanged", pickVoice); } catch { /* old browsers */ }
}

export const currentVoice = () => voice;

/** Resolves true if audio started, false if the browser could not play it. */
export function speak(text: string): Promise<boolean> {
  return new Promise(resolve => {
    try {
      if (!speechSupported) return resolve(false);
      if (!voice) pickVoice();
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "en-GB";
      u.rate = 0.9;
      if (voice) u.voice = voice;
      let started = false;
      u.onstart = () => { started = true; resolve(true); };
      u.onerror = () => { if (!started) resolve(false); };
      // Chrome drops a speak() that follows cancel() too closely
      setTimeout(() => { try { speechSynthesis.resume(); speechSynthesis.speak(u); } catch { resolve(false); } }, 60);
      setTimeout(() => { if (!started) resolve(false); }, 2000);
    } catch { resolve(false); }
  });
}

export const translateLink = (w: string) =>
  `https://translate.google.com/?sl=en&tl=fr&op=translate&text=${encodeURIComponent(w)}`;
