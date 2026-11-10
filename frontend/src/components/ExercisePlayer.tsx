import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { strings } from "../i18n";
import type { AnswerResult, MissionNext, MissionState, Question, Scoring, Unit } from "../types";
import { QuestionView } from "./QuestionView";

const DEFAULT_SCORING: Scoring = { first: 10, retry: 5, hint_cost: 3, streak_bonus: 5, streak_from: 3 };

// A session (mission or training) and its questions so far; `view` is the question on screen.
// The last question is the current one; the earlier ones are finished and can be shown again.
interface Play { mission: MissionState; questions: Question[]; view: number }

/** Exercise tab of a unit: setup (level, count, topic), mission or free training, result.
 *  Both are saved on the server: the student can pause and resume them later. */
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
  const [paused, setPaused] = useState<MissionState[]>([]);
  const [play, setPlay] = useState<Play | null>(null);
  const [result, setResult] = useState<MissionNext | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadBest = () => api.progress(unit.slug).then(p => setBest(p[0]?.best ?? {})).catch(() => undefined);
  const loadPaused = () => api.activeSessions(unit.slug).then(setPaused).catch(() => undefined);
  useEffect(() => { loadBest(); loadPaused(); }, [unit.slug]); // eslint-disable-line react-hooks/exhaustive-deps

  async function guard(fn: () => Promise<void>) {
    setError(null);
    try { await fn(); } catch (e) { setError(e instanceof ApiError ? e.message : "Erreur réseau, réessaie."); }
  }

  const begin = (mission: MissionState, questions: Question[]) => {
    setResult(null);
    setPlay({ mission, questions, view: questions.length - 1 });
  };

  const startMission = (item_keys?: string[]) => guard(async () => {
    const r = await api.startMission({ unit: unit.slug, level, count, category, item_keys });
    begin(r.mission, [r.question]);
  });

  const startTraining = (exercise: string) => guard(async () => {
    const r = await api.startTraining(unit.slug, exercise, level);
    begin(r.mission, [r.question]);
  });

  const resume = (m: MissionState) => guard(async () => {
    const r = await api.mission(m.id);
    begin(r.mission, r.questions);
  });

  const discard = (m: MissionState) => guard(async () => {
    await api.abandonMission(m.id);
    await loadPaused();
  });

  function onResult(r: AnswerResult) {
    if (r.mission) setPlay(p => (p ? { ...p, mission: r.mission! } : p));
  }

  const next = () => guard(async () => {
    if (!play) return;
    const r = await api.nextInMission(play.mission.id);
    if (r.question) {
      const questions = [...play.questions, r.question];
      setPlay({ mission: r.mission, questions, view: questions.length - 1 });
    } else { setPlay(null); setResult(r); loadBest(); loadPaused(); }
  });

  // show a finished question again; it is reloaded to get the correction and the answers given
  const goTo = (i: number) => guard(async () => {
    if (!play) return;
    const last = play.questions.length - 1;
    if (i < 0 || i > last) return;
    if (i === last) { setPlay({ ...play, view: i }); return; }
    const q = await api.question(play.questions[i].id);
    setPlay(p => p && { ...p, questions: p.questions.map((x, j) => (j === i ? q : x)), view: i });
  });

  function pause() {
    setPlay(null);
    setResult(null);
    loadPaused();
  }

  function quit() {
    if (play) api.abandonMission(play.mission.id).catch(() => undefined).finally(loadPaused);
    setPlay(null);
    setResult(null);
  }

  // ------------------------------------------------------------- playing
  if (play) {
    const { mission, questions, view } = play;
    const training = mission.mode === "training";
    const last = questions.length - 1;
    const reviewing = view < last;
    const header = (
      <>
        <div className="qhead">
          <span className="qnav">
            <button className="arrow" onClick={() => goTo(view - 1)} disabled={view === 0}
              aria-label={t.previous} title={t.previous}>◀</button>
            <span>
              {training ? `${t.question} ${view + 1}` : `${t.question} ${view + 1} / ${mission.total}`}
              {levels.length > 0 && ` · ${levels[mission.level].label}`}
            </span>
            <button className="arrow" onClick={() => goTo(view + 1)} disabled={view === last}
              aria-label={t.following} title={t.following}>▶</button>
          </span>
          <span>
            {training && <>{t.trainingStats(mission.good, mission.answered)} · </>}
            {t.score} : <strong>{mission.score}</strong>
            {mission.streak >= 2 && scoring.streak_bonus > 0 && <> · 🔥 {mission.streak}</>}
          </span>
        </div>
        {!training && <div className="bar"><span style={{ width: `${(mission.answered / mission.total) * 100}%` }} /></div>}
      </>
    );
    const current = questions[last];
    return (
      <section className="panel">
        {reviewing && (
          <>
            {header}
            <p className="feedback reviewing" style={{ margin: 0 }}>{t.reviewing(view + 1)}</p>
            <QuestionView key={`r-${questions[view].id}`} question={questions[view]} t={t} scoring={scoring}
              header={null} isLast={false} review onResult={() => undefined} onNext={() => undefined}
              onQuit={() => undefined} quitLabel="" />
            <div className="row"><button className="btn" onClick={() => goTo(last)}>{t.backToCurrent}</button></div>
          </>
        )}
        {/* the current question stays mounted while reviewing, so nothing typed is lost */}
        <div style={{ display: reviewing ? "none" : "contents" }}>
          <QuestionView key={current.id} question={current} t={t} scoring={scoring} header={header}
            isLast={!training && last + 1 >= mission.total}
            onResult={onResult} onNext={next} onQuit={quit} onPause={pause}
            quitLabel={training ? t.quitTraining : t.quitMission} />
        </div>
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
      {paused.map(m => (
        <div key={m.id} className="mission paused">
          <div>
            <h3>{m.mode === "training" ? t.pausedTraining(m.exercise ?? "") : t.pausedMission}</h3>
            <p className="muted">
              {levels.length > 0 && `${levels[m.level]?.label} · `}
              {m.mode === "training" ? t.pausedTrainingInfo(m.good, m.answered) : t.pausedInfo(m.index + 1, m.total, m.score)}
            </p>
            {m.mode === "mission" && <p className="muted small-note">{t.pausedReplace}</p>}
          </div>
          <div className="row">
            <button className="btn ghost" onClick={() => discard(m)}>{t.discard}</button>
            <button className="btn" onClick={() => resume(m)}>{t.resume}</button>
          </div>
        </div>
      ))}
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
