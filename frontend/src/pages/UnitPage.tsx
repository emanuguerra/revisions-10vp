import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { ExercisePlayer } from "../components/ExercisePlayer";
import { LessonView } from "../components/LessonView";
import type { Unit } from "../types";

const EXERCISES = "exercices";

/** Highlights the last word of the title, like the original pages. */
function Title({ text }: { text: string }) {
  const i = text.lastIndexOf(" ");
  return i < 0 ? <h1><mark>{text}</mark></h1> : <h1>{text.slice(0, i)} <mark>{text.slice(i + 1)}</mark></h1>;
}

export function UnitPage() {
  const { slug = "", tab } = useParams();
  const navigate = useNavigate();
  const [unit, setUnit] = useState<Unit | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setUnit(null);
    api.unit(slug).then(setUnit).catch(e => setError(e instanceof ApiError ? e.message : "Erreur réseau."));
  }, [slug]);

  if (error) return <p className="feedback no">{error} <Link to="/">Retour à l'accueil</Link></p>;
  if (!unit) return <p className="muted">Chargement…</p>;

  const current = tab ?? unit.lessons[0]?.slug ?? EXERCISES;
  const lesson = unit.lessons.find(l => l.slug === current);
  const go = (t: string) => navigate(`/u/${unit.slug}/${t}`);

  return (
    <div className="wrap" lang={unit.ui_lang}>
      <header className="intro">
        <Title text={unit.title} />
        <p>{unit.subtitle}</p>
        {unit.config.subtitle_fr && <p className="fr" lang="fr">{unit.config.subtitle_fr}</p>}
      </header>
      <nav className="tabs" role="tablist">
        {unit.lessons.map(l => (
          <button key={l.slug} className="tab" role="tab" aria-selected={current === l.slug} onClick={() => go(l.slug)}>{l.title}</button>
        ))}
        {unit.exercises.length > 0 && (
          <button className="tab" role="tab" aria-selected={current === EXERCISES} onClick={() => go(EXERCISES)}>
            {unit.config.exercises_title ?? "Exercices"}
          </button>
        )}
      </nav>
      {lesson && <LessonView lesson={lesson} unit={unit} />}
      {current === EXERCISES && <ExercisePlayer unit={unit} onBackToLesson={() => go(unit.lessons[0]?.slug ?? EXERCISES)} />}
    </div>
  );
}
