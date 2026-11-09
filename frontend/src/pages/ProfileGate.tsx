import { useState } from "react";
import { api, ApiError, setToken } from "../api";
import { useProfile } from "../profile";

/** First visit: create a profile (no password) or come back with a recovery code. */
export function ProfileGate() {
  const { signIn } = useProfile();
  const [nickname, setNickname] = useState("");
  const [classCode, setClassCode] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try { signIn(await api.createProfile(nickname, classCode)); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Erreur réseau, réessaie."); }
  }

  async function restore(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setToken(code.trim());
    try { signIn(await api.me()); }
    catch { setToken(null); setError("Ce code de reprise est inconnu."); }
  }

  return (
    <div className="wrap gate">
      <header className="intro">
        <h1>Révisions <mark>10e</mark></h1>
        <p>Théorie, exercices et quiz pour réviser le programme de 10e VP. Ta progression est enregistrée.</p>
      </header>
      <div className="duo">
        <form className="box" onSubmit={create}>
          <h2>Nouveau profil</h2>
          <label htmlFor="nick">Ton prénom ou un pseudo</label>
          <input id="nick" className="field" value={nickname} onChange={e => setNickname(e.target.value)} maxLength={60} required />
          <label htmlFor="cls">Code de ta classe <span className="muted">(facultatif, donné par ton enseignant·e)</span></label>
          <input id="cls" className="field" value={classCode} onChange={e => setClassCode(e.target.value)} maxLength={30} />
          <div className="row"><button className="btn" type="submit">Commencer</button></div>
        </form>
        <form className="box" onSubmit={restore}>
          <h2>J'ai déjà un profil</h2>
          <p className="muted">Entre ton code de reprise. Tu le trouves dans « Ma progression » sur ton autre appareil.</p>
          <label htmlFor="code">Code de reprise</label>
          <input id="code" className="field" value={code} onChange={e => setCode(e.target.value)} required autoCapitalize="off" spellCheck={false} />
          <div className="row"><button className="btn ghost" type="submit">Reprendre</button></div>
        </form>
      </div>
      {error && <p className="feedback no">{error}</p>}
    </div>
  );
}
