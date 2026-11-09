import { useEffect, useRef, useState, type ReactNode } from "react";
import { api, ApiError } from "../api";
import type { Strings } from "../i18n";
import { speak } from "../speech";
import type { AnswerResult, Question, Scoring, Side } from "../types";
import { TriangleFigure } from "./widgets/TriangleFigure";

interface Props {
  question: Question;
  t: Strings;
  scoring: Scoring;
  header: ReactNode;
  isLast: boolean;
  onResult: (r: AnswerResult) => void;   // every answer (to update the score header)
  onNext: () => void;
  onQuit: () => void;
  quitLabel: string;
}

const pick = <T,>(a: T[]) => a[Math.floor(Math.random() * a.length)];

/**
 * One question. The server decides whether an answer is right, how many attempts remain
 * and the points. A wrong answer can be corrected until the last attempt.
 */
export function QuestionView({ question: q, t, scoring, header, isLast, onResult, onNext, onQuit, quitLabel }: Props) {
  const [value, setValue] = useState("");
  const [eliminated, setEliminated] = useState<(number | string)[]>(q.eliminated);
  const [tries, setTries] = useState(q.tries);
  const [message, setMessage] = useState<{ kind: "retry" | "invalid"; text: string } | null>(null);
  const [final, setFinal] = useState<AnswerResult | null>(null);
  const [hint, setHint] = useState<string | null>(q.hint);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const nextRef = useRef<HTMLButtonElement>(null);
  const praise = useRef(pick(t.correct));

  useEffect(() => { inputRef.current?.focus(); }, [q.id]);
  useEffect(() => { if (final) nextRef.current?.focus(); }, [final]);

  function handle(r: AnswerResult) {
    onResult(r);
    if (r.status === "invalid") { setMessage({ kind: "invalid", text: r.message }); return; }
    setEliminated(r.eliminated);
    setTries(r.tries);
    if (r.final) {
      setFinal(r);
      setMessage(null);
      if (r.speak) speak(r.speak);
    } else {
      setMessage({ kind: "retry", text: r.message });
      setTimeout(() => inputRef.current?.select(), 0);
    }
  }

  async function run(fn: () => Promise<AnswerResult>) {
    if (busy || final) return;
    setBusy(true);
    try { handle(await fn()); }
    catch (e) { setMessage({ kind: "invalid", text: e instanceof ApiError ? e.message : "Erreur réseau, réessaie." }); }
    finally { setBusy(false); }
  }

  const submit = (v: string | number) => run(() => api.answer(q.id, v));
  const reveal = () => run(() => api.reveal(q.id));
  async function askHint() {
    try { setHint((await api.hint(q.id)).hint); } catch { /* ignore */ }
  }

  const done = !!final;
  const correctAnswer = final?.correct_answer;
  const sideState: Partial<Record<Side, "ok" | "ko">> = {};
  if (q.kind === "side") {
    eliminated.forEach(s => { sideState[s as Side] = "ko"; });
    if (done) sideState.c = "ok";
  }

  return (
    <>
      {header}
      <div className="qtype">{q.category}</div>
      <div className={`mq${q.figure ? "" : " nofig"}`}>
        <div className="mprompt" dangerouslySetInnerHTML={{ __html: q.prompt }} />
        {q.figure && (
          <div>
            <TriangleFigure {...q.figure} sideState={sideState}
              click={q.figure.click && !done}
              onSide={k => { if (!eliminated.includes(k)) submit(k); }} />
          </div>
        )}
      </div>

      {(q.kind === "number" || q.kind === "text") && (
        <form className="typein" autoComplete="off" onSubmit={e => { e.preventDefault(); if (value.trim()) submit(value); }}>
          <input ref={inputRef} id="answer" value={value} onChange={e => setValue(e.target.value)} disabled={done}
            inputMode={q.kind === "number" ? "decimal" : "text"} aria-label={t.yourAnswer} placeholder={t.yourAnswer}
            autoCapitalize="off" spellCheck={false} />
          {q.unit && <span className="unit">{q.unit}</span>}
          <button className="btn" type="submit" disabled={done || busy}>{t.check}</button>
        </form>
      )}

      {q.kind === "choice" && q.choices && (
        <div className="choices">
          {q.choices.map((c, i) => {
            const cls = done && i === correctAnswer ? " right" : eliminated.includes(i) ? " wrong" : "";
            return (
              <button key={i} className={`choice${cls}`} disabled={done || busy || eliminated.includes(i)}
                onClick={() => submit(i)}>{c}</button>
            );
          })}
        </div>
      )}

      {q.has_hint && !done && (
        <div className="row" style={{ justifyContent: "flex-start", alignItems: "center" }}>
          <button className="btn ghost small" onClick={askHint} disabled={!!hint}>{t.hint}</button>
          {hint && <span className="muted">{hint}</span>}
        </div>
      )}

      {message?.kind === "invalid" && <p className="muted" style={{ margin: 0 }}>{message.text}</p>}
      {message?.kind === "retry" && (
        <div className="feedback no">
          {message.text}
          <small>
            {t.attempt} {tries} / {q.max_tries}. {scoring.retry > 0 ? t.retryPoints(scoring.retry) : t.retryNoPoints}
          </small>
          <div className="row" style={{ justifyContent: "flex-start", marginTop: 10 }}>
            <button className="btn ghost small" onClick={reveal}>{t.reveal}</button>
          </div>
        </div>
      )}

      {final && (
        <div>
          <div className={`feedback ${final.status === "correct" ? "ok" : "no"}`}>
            {final.status === "correct"
              ? <>{tries > 0 ? t.corrected : praise.current}
                  {final.points > 0 && <> +{final.points} {t.points}</>}
                  {final.mission && final.mission.streak >= scoring.streak_from && scoring.streak_bonus > 0 &&
                    <> · {t.series} {final.mission.streak} 🔥</>}</>
              : t.wrong}
            {final.summary ? (
              // vocabulary: short recap line, plus the right word after a mistake
              <>
                {final.status !== "correct" && final.explain && <> <span dangerouslySetInnerHTML={{ __html: final.explain }} /></>}
                <small dangerouslySetInnerHTML={{ __html: final.summary }} />
              </>
            ) : final.explain && <div className="calc" dangerouslySetInnerHTML={{ __html: final.explain }} />}
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <button ref={nextRef} className="btn" onClick={onNext}>{isLast ? t.seeResult : t.next}</button>
          </div>
        </div>
      )}

      <div className="row"><button className="btn ghost small" onClick={onQuit}>{quitLabel}</button></div>
    </>
  );
}
