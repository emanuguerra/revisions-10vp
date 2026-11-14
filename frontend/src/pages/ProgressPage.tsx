import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useProfile } from "../profile";
import { BadgeBoard, useRewards } from "../rewards";
import type { UnitProgress } from "../types";

export function ProgressPage() {
  const { profile, signOut } = useProfile();
  const [rows, setRows] = useState<UnitProgress[] | null>(null);
  const [copied, setCopied] = useState(false);
  const [confirmOut, setConfirmOut] = useState(false);

  const { refresh } = useRewards();
  useEffect(() => { api.progress().then(setRows); refresh(); }, [refresh]);

  async function copy() {
    try { await navigator.clipboard.writeText(profile?.token ?? ""); setCopied(true); }
    catch { /* the code stays selectable */ }
  }

  return (
    <div className="wrap">
      <header className="intro">
        <h1>Ma <mark>progression</mark></h1>
        <p>{profile?.nickname}{profile?.class_code ? ` · classe ${profile.class_code}` : ""}</p>
      </header>

      <section className="box">
        <h2>Mes badges</h2>
        <BadgeBoard />
      </section>

      <section className="box">
        <h2>Par chapitre</h2>
        {!rows ? <p className="muted">Chargement…</p> : (
          <div className="tablewrap">
            <table className="when">
              <thead><tr><th>Chapitre</th><th>Questions</th><th>Justes du premier coup</th><th>Missions</th><th>Records</th></tr></thead>
              <tbody>
                {rows.map(r => (
                  <tr key={r.unit}>
                    <td><Link to={`/u/${r.unit}`}>{r.title}</Link></td>
                    <td className="num">{r.answered}</td>
                    <td className="num">{r.answered ? `${Math.round((r.correct_first / r.answered) * 100)} %` : "—"}</td>
                    <td className="num">{r.missions_done}</td>
                    <td>{Object.keys(r.best).length ? Object.entries(r.best).map(([l, s]) => `niv. ${+l + 1} : ${s}`).join(" · ") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="box">
        <h2>Code de reprise</h2>
        <p>Garde ce code pour retrouver ta progression sur un autre appareil ou un autre navigateur.</p>
        <div className="tester">
          <code className="token">{profile?.token}</code>
          <button className="btn small" onClick={copy}>{copied ? "Copié" : "Copier"}</button>
        </div>
        <div className="row" style={{ justifyContent: "flex-start" }}>
          {!confirmOut
            ? <button className="btn ghost small" onClick={() => setConfirmOut(true)}>Changer de profil</button>
            : <>
                <span className="muted">As-tu noté ton code de reprise ?</span>
                <button className="btn small" onClick={signOut}>Oui, changer de profil</button>
                <button className="btn ghost small" onClick={() => setConfirmOut(false)}>Annuler</button>
              </>}
        </div>
      </section>
    </div>
  );
}
