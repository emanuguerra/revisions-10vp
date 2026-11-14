import { useEffect, useState } from "react";
import { currentVoice, langName, say, setPreferredVoice, speechSupported, voicesFor } from "../../speech";

const LANGS = {
  en: { speech: "en-GB", sample: "Hello, I am a nurse." },
  de: { speech: "de-DE", sample: "Hallo! Wie geht's? Mir geht's gut." },
  fr: { speech: "fr-FR", sample: "Bonjour, comment ça va ?" },
};
type Lang = keyof typeof LANGS;

/** Where to get a missing voice, for the computers the family uses. */
function InstallHelp({ lang }: { lang: Lang }) {
  const name = langName(LANGS[lang].speech);
  return (
    <details className="small-note">
      <summary>Comment ajouter une voix {name} ?</summary>
      <ul>
        <li><strong>Le plus simple :</strong> ouvre l'application dans <strong>Google Chrome</strong> ou <strong>Microsoft Edge</strong>, qui ont des voix de bonne qualité dans toutes les langues.</li>
        <li><strong>Mac :</strong> Réglages Système → Accessibilité → Contenu énoncé → Voix du système → Gérer les voix, puis coche une voix {name} (par exemple {lang === "de" ? "Anna" : lang === "en" ? "Daniel" : "Thomas"}). Redémarre Safari.</li>
        <li><strong>Windows :</strong> Paramètres → Heure et langue → Voix → Ajouter des voix, puis choisis {lang === "de" ? "Deutsch" : lang === "en" ? "English (United Kingdom)" : "Français"}. Redémarre le navigateur.</li>
      </ul>
    </details>
  );
}

/** One language: the voice used (the student can choose another one) and a test button. */
function LangRow({ lang, sample }: { lang: Lang; sample?: string }) {
  const { speech } = LANGS[lang];
  const [voices, setVoices] = useState(() => voicesFor(speech));
  const [voice, setVoice] = useState(() => currentVoice(speech)?.name ?? "");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const refresh = () => { setVoices(voicesFor(speech)); setVoice(currentVoice(speech)?.name ?? ""); };
    refresh();
    try { speechSynthesis.addEventListener("voiceschanged", refresh); } catch { /* old browsers */ }
    return () => { try { speechSynthesis.removeEventListener("voiceschanged", refresh); } catch { /* old browsers */ } };
  }, [speech]);

  async function test() {
    setMsg("Lecture…");
    const r = await say(sample ?? LANGS[lang].sample, speech);
    setMsg(r === "ok" ? "✅ Si tu n'entends rien, vérifie le volume." : r === "novoice" ? "" : "❌ Le navigateur n'a pas lancé le son.");
  }

  return (
    <div className="voice-row">
      <strong>Voix {langName(speech)}</strong>
      {voices.length ? (
        <>
          <select className="field" value={voice} aria-label={`Voix ${langName(speech)}`}
            onChange={e => { setVoice(e.target.value); setPreferredVoice(speech, e.target.value); }}>
            {voices.map(v => <option key={v.name} value={v.name}>{v.name} ({v.lang})</option>)}
          </select>
          <button className="btn small" onClick={test}>Tester</button>
          {msg && <span>{msg}</span>}
        </>
      ) : (
        <span className="voice-missing">❌ Aucune voix {langName(speech)} sur ce navigateur : les mots seraient lus avec un mauvais accent.</span>
      )}
      {!voices.length && <InstallHelp lang={lang} />}
    </div>
  );
}

/**
 * Checks the voices of this unit: `lang` (en or de) for the words, and French for the translations.
 * `sample` overrides the sentence played for `lang`.
 */
export function SoundCheck({ lang = "en", sample }: { lang?: "en" | "de"; sample?: string }) {
  if (!speechSupported) {
    return (
      <div className="soundbox">
        <p>❌ Ce navigateur ne sait pas lire à voix haute. Utilise Google Chrome, ou les liens <strong>Google Traduction ↗</strong> des cartes.</p>
      </div>
    );
  }
  return (
    <div className="soundbox voices">
      <p>🔊 Vérifie la prononciation sur cet ordinateur. Choisis la voix qui te plaît : les voix « Google », « Natural » ou « Premium » sont les plus naturelles.</p>
      <LangRow lang={lang} sample={sample} />
      <LangRow lang="fr" />
    </div>
  );
}
