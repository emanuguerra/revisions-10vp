import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { strings } from "../i18n";
import type { AnswerResult, MissionNext, MissionState, Question, Scoring, Unit } from "../types";
import { QuestionView } from "./QuestionView";

const DEFAULT_SCORING: Scoring = { first: 10, retry: 5, hint_cost: 3, streak_bonus: 5, streak_from: 3 };

type Play =
  | { mode: "mission"; mission: MissionState; question: Question }
  | { mode: "training"; exercise: string; question: Question; score: number; good: number; done: number; streak: number };

/** Exercise tab of a unit: setup (level, count, topic), mission or free training, result. */
export function ExercisePlayer({ unit, onBackToLesson }: { unit: Unit; onBackToLesson: () => void }) {
  const t = strings(unit.ui_lang);
  const cfg = unit.config;
  const mcfg = cfg.mission ?? { mode: "sequence" };
  const scoring = { ...DEFAULT_SCORING, ...cfg.scoring };
  const levels = cfg.levels ?? [];
  const [level, setLevel] = useState(0);
  const [count, setCount] = useState(mcfg.counts?.[0]);
  const [category, setCategory] = useState<string | null>(null);
  const [best, setBest] = useState<Record<string, number>>({});
  const [play, setPlay] = useState<Play | null>(null);
  const [result, setResult] = useState<MissionNext | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadBest = () => api.progress(unit.slug).then(p => setBest(p[0]?.best ?? {})).catch(() => undefined);
  useEffect(() => { loadBest(); }, [unit.slug]); // eslint-disable-line react-hooks/exhaustive-deps

  async function guard(fn: () => Promise<void>) {
    setError(null);
    try { await fn(); } catch (e) { setError(e instanceof ApiError ? e.message : "Erreur réseau, réessaie."); }
  }

  const startMission = (item_keys?: string[]) => guard(async () => {
    const r = await api.startMission({ unit: unit.slug, level, count, category, item_keys });
    setResult(null);
    setPlay({ mode: "mission", mission: r.mission, question: r.question });
  });

  const startTraining = (exercise: string) => guard(async () => {
    const q = await api.trainingQuestion(unit.slug, exercise, level);
    setResult(null);
    setPlay({ mode: "training", exercise, question: q, score: 0, good: 0, done: 0, streak: 0 });
  });

  function onResult(r: AnswerResult) {
    setPlay(p => {
      if (!p) return p;
      if (p.mode === "mission") return r.mission ? { ...p, mission: r.mission } : p;
      if (!r.final) return r.status === "retry" ? { ...p, streak: 0 } : p;
      const firstTry = r.status === "correct" && r.tries === 0;
      return { ...p, score: p.score + r.points, done: p.done + 1, good: p.good + (r.status === "correct" ? 1 : 0),
        streak: firstTry ? p.streak + 1 : 0 };
    });
  }

  const next = () => guard(async () => {
    if (!play) return;
    if (play.mode === "training") {
      const q = await api.trainingQuestion(unit.slug, play.exercise, level);
      setPlay({ ...play, question: q });
      return;
    }
    const r = await api.nextInMission(play.mission.id);
    if (r.question) setPlay({ ...play, mission: r.mission, question: r.question });
    else { setPlay(null); setResult(r); loadBest(); }
  });

  function quit() {
    if (play?.mode === "mission") api.abandonMission(play.mission.id).catch(() => undefined);
    setPlay(null);
    setResult(null);
  }

  // ------------------------------------------------------------- playing
  if (play) {
    const mission = play.mode === "mission" ? play.mission : null;
    const score = mission ? mission.score : play.mode === "training" ? play.score : 0;
    const streak = mission ? mission.streak : play.mode === "training" ? play.streak : 0;
    const header = (
      <>
        <div className="qhead">
          <span>
            {mission ? `${t.question} ${mission.index + 1} / ${mission.total}`
              : play.mode === "training" ? t.trainingStats(play.good, play.done) : ""}
            {levels.length > 0 && ` · ${levels[level].label}`}
          </span>
          <span>{t.score} : <strong>{score}</strong>{streak >= 2 && scoring.streak_bonus > 0 && <> · 🔥 {streak}</>}</span>
        </div>
        {mission && <div className="bar"><span style={{ width: `${(mission.index / mission.total) * 100}%` }} /></div>}
      </>
    );
    return (
      <section className="panel">
        <QuestionView key={play.question.id} question={play.question} t={t} scoring={scoring} header={header}
          isLast={!!mission && mission.index + 1 >= mission.total}
          onResult={onResult} onNext={next} onQuit={quit} quitLabel={mission ? t.quitMission : t.quitTraining} />
        {error && <p className="feedback no">{error}</p>}
      </section>
    );
  }

  // ------------------------------------------------------------- result
  if (result) {
    const m = result.mission;
    const ratio = m.total ? m.good / m.total : 0;
    const stars = ratio >= 0.9 ? 3 : ratio >= 0.7 ? 2 : ratio >= 0.5 ? 1 : 0;
    const fraction = mcfg.score_display === "fraction";
    const badge = mcfg.badges?.[stars] ?? "";
    const record = !fraction && (result.previous_best ?? 0) < m.score;
    const mistakes = result.mistakes.filter(x => x.summary);
    return (
      <section className="panel">
        <div className="qtype">{t.missionDone}{levels.length > 0 && ` · ${levels[m.level].label}`}</div>
        {!fraction && (
          <div className="stars" aria-label={`${stars} étoiles sur 3`}>{"★".repeat(stars)}<span className="muted">{"☆".repeat(3 - stars)}</span></div>
        )}
        <div className="score">{fraction ? `${m.good_first} / ${m.total}` : `${m.score} pts`}</div>
        <h2>{badge}</h2>
        <p style={{ margin: 0 }}>
          {fraction ? t.goodAnswers(m.good_first, m.total) : t.goodAnswers(m.good, m.total)}{" "}
          {!fraction && (record ? <strong>{t.newRecord}</strong> : t.yourRecord(result.previous_best ?? 0))}
        </p>
        {!fraction && stars === 3 && m.level < levels.length - 1 && <p className="muted" style={{ margin: 0 }}>{t.readyFor(levels[m.level + 1].label)}</p>}
        {mcfg.review_mistakes && mistakes.length > 0 && (
          <>
            <h3>{t.mistakes}</h3>
            <ul className="review">
              {mistakes.map((x, i) => (
                <li key={i}><span dangerouslySetInnerHTML={{ __html: x.summary ?? "" }} />
                  {x.given && <span className="muted"> ({t.youAnswered}: {x.given})</span>}</li>
              ))}
            </ul>
          </>
        )}
        <div className="row">
          <button className="btn ghost" onClick={onBackToLesson}>{t.backToLesson}</button>
          {mcfg.review_mistakes && mistakes.length > 0 && (
            <button className="btn ghost" onClick={() => startMission(mistakes.map(x => x.item_key!).filter(Boolean))}>{t.practiseMistakes}</button>
          )}
          <button className="btn ghost" onClick={() => setResult(null)}>{t.menu}</button>
          <button className="btn" onClick={() => startMission()}>{t.again}</button>
        </div>
        {error && <p className="feedback no">{error}</p>}
      </section>
    );
  }

  // ------------------------------------------------------------- setup
  const cats = cfg.categories ?? {};
  return (
    <section className="panel">
      {levels.length > 0 && (
        <>
          <h2>{t.chooseLevel}</h2>
          <div className="chips">
            {levels.map((l, i) => <button key={i} className="chip" aria-pressed={i === level} onClick={() => setLevel(i)}>{l.label}</button>)}
          </div>
          <p className="muted" style={{ margin: 0 }}>{levels[level].info}</p>
        </>
      )}
      {mcfg.filter === "category" && (
        <div className="setup">
          <span className="label">{t.topic}</span>
          <div className="chips">
            <button className="chip" aria-pressed={category === null} onClick={() => setCategory(null)}>{t.all}</button>
            {Object.entries(cats).map(([k, v]) => (
              <button key={k} className="chip" aria-pressed={category === k} onClick={() => setCategory(k)}>{v}</button>
            ))}
          </div>
        </div>
      )}
      {mcfg.counts && (
        <div className="setup">
          <span className="label">{t.count}</span>
          <div className="chips">
            {mcfg.counts.map(n => <button key={n} className="chip" aria-pressed={n === count} onClick={() => setCount(n)}>{n}</button>)}
          </div>
        </div>
      )}
      <div className="mission">
        <div>
          <h3>{mcfg.title}</h3>
          {mcfg.description && <p className="muted">{mcfg.description}</p>}
          {mcfg.score_display !== "fraction" && <p>{t.record} : <strong>{best[String(level)] ?? 0} {t.points}</strong></p>}
        </div>
        <button className="btn" onClick={() => startMission()}>{t.start}</button>
      </div>
      {cfg.training && (
        <>
          <h3>{t.training}</h3>
          <p className="muted" style={{ margin: 0 }}>{t.trainingHelp}</p>
          <div className="typegrid">
            {unit.exercises.map(e => <button key={e.key} className="choice" onClick={() => startTraining(e.key)}>{e.title}</button>)}
          </div>
        </>
      )}
      {error && <p className="feedback no">{error}</p>}
    </section>
  );
}
