// Focus sessions: 15 or 20 minutes of work, then a 5-minute break with ideas and videos on the
// theme of the chapter. The session survives a page reload (kept in this browser).
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { api } from "./api";
import { useRewards } from "./rewards";
import type { BreakVideo } from "./types";

const KEY = "r10-focus";
const BREAK_MIN = 5;

interface State { phase: "focus" | "break"; minutes: number; endsAt: number }
interface Ctx { state: State | null; start: (minutes: number) => void; stop: () => void }
const FocusContext = createContext<Ctx>({ state: null, start: () => {}, stop: () => {} });

function load(): State | null {
  try { return JSON.parse(localStorage.getItem(KEY) ?? "null"); } catch { return null; }
}
function save(s: State | null) {
  try { s ? localStorage.setItem(KEY, JSON.stringify(s)) : localStorage.removeItem(KEY); } catch { /* private mode */ }
}

const mmss = (ms: number) => {
  const s = Math.max(0, Math.ceil(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

function useNow(active: boolean) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!active) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [active]);
  return now;
}

export function FocusProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State | null>(load);
  const { refresh } = useRewards();
  const now = useNow(!!state);
  const set = (s: State | null) => { save(s); setState(s); };

  // End of the focus time: count the session, then start the break
  useEffect(() => {
    if (state?.phase === "focus" && now >= state.endsAt) {
      set({ phase: "break", minutes: state.minutes, endsAt: Date.now() + BREAK_MIN * 60_000 });
      api.focusDone(state.minutes).then(r => refresh(r)).catch(() => { /* still a break */ });
    }
  }, [now, state]);  // eslint-disable-line react-hooks/exhaustive-deps

  const start = (minutes: number) => set({ phase: "focus", minutes, endsAt: Date.now() + minutes * 60_000 });
  const stop = () => set(null);

  return (
    <FocusContext.Provider value={{ state, start, stop }}>
      {children}
      {state?.phase === "break" && <BreakScreen state={state} now={now} onAgain={() => start(state.minutes)} onStop={stop} />}
    </FocusContext.Provider>
  );
}

export const useFocus = () => useContext(FocusContext);

/** In the navigation: start a session, or the time left. */
export function FocusControl() {
  const { state, start, stop } = useFocus();
  const now = useNow(!!state);
  const [open, setOpen] = useState(false);

  if (state?.phase === "focus") {
    const left = state.endsAt - now;
    const pct = 100 - Math.round((left / (state.minutes * 60_000)) * 100);
    return (
      <span className="focus-pill" title="Session de concentration en cours">
        <span aria-hidden="true">⏱️</span>
        <span className="focus-time">{mmss(left)}</span>
        <span className="xp-bar" aria-hidden="true"><span style={{ width: `${pct}%` }} /></span>
        <button className="focus-stop" onClick={stop} aria-label="Arrêter la session">✕</button>
      </span>
    );
  }
  return (
    <span className="focus-start">
      <button className="subj" onClick={() => setOpen(o => !o)} aria-expanded={open}>⏱️ Concentration</button>
      {open && (
        <span className="focus-menu">
          <span className="muted">Travaille sans distraction, puis fais une pause de {BREAK_MIN} minutes :</span>
          {[15, 20].map(m => (
            <button key={m} className="btn small" onClick={() => { start(m); setOpen(false); }}>{m} minutes</button>
          ))}
        </span>
      )}
    </span>
  );
}

const IDEAS = [
  "🙆 Lève-toi et étire-toi : bras en haut, puis touche tes pieds.",
  "💧 Bois un verre d'eau.",
  "👀 Regarde loin par la fenêtre pendant 20 secondes : tes yeux se reposent.",
  "🗣️ Raconte à quelqu'un trois choses que tu viens d'apprendre.",
  "🚶 Fais le tour de la maison ou du jardin.",
];

const GENERIC: Record<string, BreakVideo[]> = {
  allemand: [{ title: "Chansons pour apprendre l'allemand", search: "Deutsch lernen Lieder Kinder" }],
  anglais: [{ title: "Songs to learn English", search: "learn English songs for teens" }],
  maths: [{ title: "Maths en vidéo", search: "mathématiques explication collège" }],
};

/** YouTube links become an embedded video; other entries open a YouTube search. */
function embedUrl(url: string): string | null {
  const m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]{11})/);
  return m ? `https://www.youtube-nocookie.com/embed/${m[1]}` : null;
}

function Videos() {
  const { pathname } = useLocation();
  const slug = pathname.match(/^\/u\/([^/]+)/)?.[1];
  const [videos, setVideos] = useState<BreakVideo[] | null>(null);
  const [playing, setPlaying] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) { setVideos([]); return; }
    api.unit(slug).then(u => setVideos(u.config.break_videos ?? GENERIC[u.subject] ?? [])).catch(() => setVideos([]));
  }, [slug]);

  if (!videos?.length) return null;
  return (
    <div className="break-videos">
      <h3>📺 Une vidéo sur le thème ?</h3>
      {playing && (
        <div className="video-frame">
          <iframe src={playing} title="Vidéo" allow="encrypted-media; picture-in-picture" allowFullScreen />
        </div>
      )}
      <ul>
        {videos.map(v => {
          const embed = v.url ? embedUrl(v.url) : null;
          const href = v.url ?? `https://www.youtube.com/results?search_query=${encodeURIComponent(v.search ?? v.title)}`;
          return (
            <li key={v.title}>
              {embed
                ? <button className="btn ghost small" onClick={() => setPlaying(embed)}>▶ {v.title}</button>
                : <a href={href} target="_blank" rel="noopener">▶ {v.title} ↗</a>}
            </li>
          );
        })}
      </ul>
      <p className="muted small-note">Une ou deux vidéos courtes, puis on se remet au travail !</p>
    </div>
  );
}

function BreakScreen({ state, now, onAgain, onStop }: { state: State; now: number; onAgain: () => void; onStop: () => void }) {
  const left = state.endsAt - now;
  const over = left <= 0;
  const [idea] = useState(() => IDEAS[Math.floor(Math.random() * IDEAS.length)]);
  return (
    <div className="break-overlay" role="dialog" aria-modal="true" aria-labelledby="break-title">
      <div className="break-box">
        <p className="break-emoji" aria-hidden="true">🎉</p>
        <h2 id="break-title">Bravo, {state.minutes} minutes de concentration !</h2>
        <p>+30 XP. C'est l'heure de la pause : ton cerveau range ce que tu viens d'apprendre.</p>
        <p className="break-time">{over ? "Pause terminée" : `Pause : ${mmss(left)}`}</p>
        <p className="break-idea">{idea}</p>
        <Videos />
        <div className="row">
          <button className="btn ghost" onClick={onStop}>Terminer pour aujourd'hui</button>
          <button className="btn" onClick={onAgain} disabled={!over}>
            {over ? `C'est reparti pour ${state.minutes} minutes` : "Profite encore de ta pause…"}
          </button>
        </div>
      </div>
    </div>
  );
}
