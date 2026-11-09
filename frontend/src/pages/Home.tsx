import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useProfile } from "../profile";
import type { Subject, UnitProgress } from "../types";

export function Home() {
  const { profile } = useProfile();
  const [subjects, setSubjects] = useState<Subject[] | null>(null);
  const [progress, setProgress] = useState<Record<string, UnitProgress>>({});

  useEffect(() => {
    api.subjects().then(setSubjects);
    api.progress().then(p => setProgress(Object.fromEntries(p.map(x => [x.unit, x])))).catch(() => undefined);
  }, []);

  if (!subjects) return <p className="muted">Chargement…</p>;

  return (
    <div className="wrap">
      <header className="intro">
        <h1>Salut {profile?.nickname} !</h1>
        <p>Choisis une branche et un chapitre. Chaque chapitre a une partie théorie et des exercices.</p>
      </header>
      <div className="subjects-grid">
        {subjects.map(s => (
          <section key={s.slug} className="subject" style={{ "--subject": s.color } as React.CSSProperties}>
            <h2><span className="dot" aria-hidden="true" />{s.title}</h2>
            {s.units.length > 0 && (
              <ul className="unit-list">
                {s.units.map(u => {
                  const p = progress[u.slug];
                  const best = p ? Math.max(0, ...Object.values(p.best)) : 0;
                  return (
                    <li key={u.slug}>
                      <Link to={`/u/${u.slug}`} className="unit-link">
                        <span className="unit-title">{u.title}</span>
                        {p && p.answered > 0 && (
                          <span className="pill">{p.answered} question{p.answered > 1 ? "s" : ""}{best > 0 ? ` · record ${best}` : ""}</span>
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
            {s.planned.length > 0 && (
              <ul className="planned">
                {s.planned.map(t => <li key={t}>{t} <span className="soon">Bientôt</span></li>)}
              </ul>
            )}
            {s.units.length === 0 && s.planned.length === 0 && <p className="muted" style={{ margin: 0 }}>Bientôt</p>}
          </section>
        ))}
      </div>
    </div>
  );
}
