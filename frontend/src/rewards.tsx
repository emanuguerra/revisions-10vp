// XP, level and badges of the student (computed by the server, see backend/app/rewards.py).
// `refresh()` after an answer or a focus session: a new badge or level shows a toast.
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { api } from "./api";
import type { Rewards } from "./types";

interface Ctx { rewards: Rewards | null; refresh: (next?: Rewards) => void }
const RewardsContext = createContext<Ctx>({ rewards: null, refresh: () => {} });

interface Toast { id: number; icon: string; title: string; text: string }

export function RewardsProvider({ children }: { children: ReactNode }) {
  const [rewards, setRewards] = useState<Rewards | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const last = useRef<Rewards | null>(null);

  const show = (t: Omit<Toast, "id">) => {
    const id = Date.now() + Math.random();
    setToasts(ts => [...ts, { ...t, id }]);
    setTimeout(() => setToasts(ts => ts.filter(x => x.id !== id)), 6000);
  };

  const apply = useCallback((r: Rewards) => {
    const before = last.current;
    if (before) {   // no toast on the first load: only for what was just earned
      const had = new Set(before.badges.filter(b => b.earned).map(b => b.id));
      r.badges.filter(b => b.earned && !had.has(b.id))
        .forEach(b => show({ icon: b.icon, title: "Nouveau badge !", text: `${b.title} : ${b.description}` }));
      if (r.level > before.level) show({ icon: "⬆️", title: `Niveau ${r.level} !`, text: `Tu es maintenant ${r.level_title}.` });
    }
    last.current = r;
    setRewards(r);
  }, []);

  const refresh = useCallback((next?: Rewards) => {
    if (next) apply(next);
    else api.rewards().then(apply).catch(() => { /* rewards are a bonus: never block the work */ });
  }, [apply]);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <RewardsContext.Provider value={{ rewards, refresh }}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map(t => (
          <div key={t.id} className="toast">
            <span className="toast-icon" aria-hidden="true">{t.icon}</span>
            <span><strong>{t.title}</strong><br />{t.text}</span>
          </div>
        ))}
      </div>
    </RewardsContext.Provider>
  );
}

export const useRewards = () => useContext(RewardsContext);

/** Level and XP bar, in the navigation. */
export function XpChip() {
  const { rewards: r } = useRewards();
  if (!r) return null;
  const pct = Math.round(((r.xp - r.level_start) / (r.next_level - r.level_start)) * 100);
  const earned = r.badges.filter(b => b.earned).length;
  return (
    <Link to="/progression" className="xp-chip" title={`${r.xp} XP · encore ${r.next_level - r.xp} XP pour le niveau ${r.level + 1}`}>
      <span className="xp-level">Niv. {r.level}</span>
      <span className="xp-bar" aria-hidden="true"><span style={{ width: `${pct}%` }} /></span>
      <span className="xp-badges">🏅 {earned}</span>
      {r.stats.days > 1 && <span className="xp-days" title="Jours de suite">🔥 {r.stats.days}</span>}
    </Link>
  );
}

/** Level, XP and every badge, earned or still to win: on the progress page. */
export function BadgeBoard() {
  const { rewards: r } = useRewards();
  if (!r) return <p className="muted">Chargement…</p>;
  const pct = Math.round(((r.xp - r.level_start) / (r.next_level - r.level_start)) * 100);
  return (
    <>
      <div className="level-card">
        <div className="level-num">{r.level}</div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <strong>Niveau {r.level} · {r.level_title}</strong>
          <div className="xp-bar big" aria-hidden="true"><span style={{ width: `${pct}%` }} /></div>
          <span className="muted">{r.xp} XP · encore {r.next_level - r.xp} XP pour le niveau {r.level + 1}</span>
        </div>
      </div>
      <p className="muted small-note">
        +10 XP par réponse juste du premier coup, +5 après correction, +20 par mission terminée,
        +30 par session de concentration.
      </p>
      <div className="badges">
        {r.badges.map(b => (
          <div key={b.id} className={`badge${b.earned ? " earned" : ""}`} title={b.description}>
            <span className="badge-icon" aria-hidden="true">{b.earned ? b.icon : "🔒"}</span>
            <strong>{b.title}</strong>
            <span className="muted">{b.description}</span>
            {!b.earned && (
              <span className="badge-progress" aria-label={`${b.value} sur ${b.goal}`}>
                <span style={{ width: `${Math.round((b.value / b.goal) * 100)}%` }} />
              </span>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
