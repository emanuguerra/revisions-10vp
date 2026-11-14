// Online installations can require a shared access code (ACCESS_CODE on the server).
// It is asked once and kept in this browser.
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { api, setAccess } from "./api";

export function AccessGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<"checking" | "ok" | "needed">("checking");
  const [code, setCode] = useState("");
  const [error, setError] = useState(false);

  const check = () => api.access()
    .then(r => setState(!r.required || r.ok ? "ok" : "needed"))
    .catch(() => setState("ok"));   // server unreachable: let the app show its own errors

  useEffect(() => {
    check();
    const again = () => setState("needed");
    window.addEventListener("r10-access-needed", again);
    return () => window.removeEventListener("r10-access-needed", again);
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setAccess(code.trim());
    const r = await api.access().catch(() => null);
    if (r && (!r.required || r.ok)) { setError(false); setState("ok"); window.location.reload(); }
    else setError(true);
  }

  if (state === "checking") return <p className="muted">Chargement…</p>;
  if (state === "ok") return <>{children}</>;
  return (
    <div className="wrap gate">
      <header className="intro">
        <h1>Révisions <mark>10e</mark></h1>
        <p>Cette application est privée. Entre le code d'accès qu'on t'a donné.</p>
      </header>
      <form className="box" onSubmit={submit} style={{ maxWidth: 420 }}>
        <label htmlFor="access">Code d'accès</label>
        <input id="access" className="field" value={code} onChange={e => setCode(e.target.value)}
          autoComplete="off" autoCapitalize="off" spellCheck={false} required autoFocus />
        {error && <p className="feedback no">Ce code n'est pas le bon.</p>}
        <div className="row"><button className="btn" type="submit">Entrer</button></div>
      </form>
    </div>
  );
}
