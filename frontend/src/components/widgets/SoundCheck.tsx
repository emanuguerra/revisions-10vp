import { useState, type ReactNode } from "react";
import { currentVoice, englishVoices, speak, speechSupported } from "../../speech";

export function SoundCheck() {
  const [msg, setMsg] = useState<ReactNode>("🔊 Check that pronunciation works on this computer. · Vérifie que le son fonctionne.");

  async function test() {
    if (!speechSupported) {
      setMsg(<>❌ This browser has no speech feature. Use the <strong>Google Translate ↗</strong> links on the cards, or use Chrome or Edge.</>);
      return;
    }
    setMsg("Playing “Hello, I am a nurse”…");
    const ok = await speak("Hello, I am a nurse.");
    const n = englishVoices().length, v = currentVoice();
    if (ok) setMsg(`✅ Sound started (${n} English voice${n === 1 ? "" : "s"} found${v ? ": " + v.name : ""}). If you heard nothing, check the volume of your computer and of the browser tab.`);
    else if (n === 0) setMsg(<>❌ No English voice is installed in this browser. Use Chrome or Edge, or the <strong>Google Translate ↗</strong> links on the cards.</>);
    else setMsg(<>❌ The browser did not start the sound. Use Chrome or Edge, or the <strong>Google Translate ↗</strong> links on the cards.</>);
  }

  return (
    <div className="soundbox">
      <p>{msg}</p>
      <button className="btn small" onClick={test}>Test sound</button>
    </div>
  );
}
