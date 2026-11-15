import { marked } from "marked";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { HtmlContent } from "../components/LessonView";
import type { Subject, Unit, WikiBrief, WikiHit, WikiPage as Page, WikiTheme } from "../types";

/** Knowledge base: themes by subject, a search box, one page at a time (/wiki/<subject>/<theme>/<page>). */
export function WikiPage() {
  const path = useParams()["*"] ?? "";
  const [params, setParams] = useSearchParams();
  const unitFilter = params.get("unit") ?? undefined;
  const [themes, setThemes] = useState<WikiTheme[] | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<WikiHit[] | null>(null);

  useEffect(() => { api.wiki(unitFilter).then(setThemes); }, [unitFilter]);
  useEffect(() => { api.subjects().then(setSubjects); }, []);
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) { setHits(null); return; }
    const t = setTimeout(() => api.wikiSearch(q).then(setHits), 250);
    return () => clearTimeout(t);
  }, [query]);

  const subjectTitle = useMemo(() => Object.fromEntries(subjects.map(s => [s.slug, s.title])), [subjects]);
  const unitTitle = useMemo(
    () => Object.fromEntries(subjects.flatMap(s => s.units.map(u => [u.slug, u.title]))), [subjects]);

  return (
    <div className={path ? "wiki has-page" : "wiki"}>
      <aside className="wiki-side">
        <input className="field" type="search" placeholder="Chercher une notion…" value={query}
          onChange={e => setQuery(e.target.value)} aria-label="Chercher dans les fiches" />
        {hits ? <Hits hits={hits} onPick={() => setQuery("")} /> : (
          <>
            {unitFilter && (
              <p className="wiki-note">Fiches de « {unitTitle[unitFilter] ?? unitFilter} » ·{" "}
                <button className="linkish" onClick={() => setParams({})}>toutes les fiches</button></p>
            )}
            {themes === null ? <p className="muted">Chargement…</p> : <Tree themes={themes} current={path} subjectTitle={subjectTitle} />}
          </>
        )}
      </aside>
      <main className="wiki-main">
        {path ? <PageView key={path} path={path} subjectTitle={subjectTitle} unitTitle={unitTitle} />
          : <Index themes={themes} subjectTitle={subjectTitle} />}
      </main>
    </div>
  );
}

function Tree({ themes, current, subjectTitle }: { themes: WikiTheme[]; current: string; subjectTitle: Record<string, string> }) {
  if (themes.length === 0) return <p className="muted">Aucune fiche pour l'instant.</p>;
  let lastSubject = "";
  return (
    <nav className="wiki-tree" aria-label="Fiches">
      {themes.map(t => {
        const head = t.subject !== lastSubject ? <h3>{subjectTitle[t.subject] ?? t.subject}</h3> : null;
        lastSubject = t.subject;
        const open = t.pages.some(p => p.path === current) || !current;
        return (
          <div key={`${t.subject}/${t.slug}`}>
            {head}
            <details open={open}>
              <summary>{t.title} <span className="pill">{t.pages.length}</span></summary>
              <ul>
                {t.pages.map(p => (
                  <li key={p.path}><Link to={`/wiki/${p.path}`} aria-current={p.path === current ? "page" : undefined}>{p.title}</Link></li>
                ))}
              </ul>
            </details>
          </div>
        );
      })}
    </nav>
  );
}

function Hits({ hits, onPick }: { hits: WikiHit[]; onPick: () => void }) {
  if (hits.length === 0) return <p className="muted">Rien trouvé. Essaie un autre mot.</p>;
  return (
    <ul className="wiki-hits">
      {hits.map(h => (
        <li key={h.path}><Link to={`/wiki/${h.path}`} onClick={onPick}><strong>{h.title}</strong><span>{h.summary}</span></Link></li>
      ))}
    </ul>
  );
}

function Index({ themes, subjectTitle }: { themes: WikiTheme[] | null; subjectTitle: Record<string, string> }) {
  return (
    <section className="wrap">
      <header className="intro">
        <h1>Fiches de <mark>révision</mark></h1>
        <p>Une fiche par notion : l'essentiel à savoir, les erreurs fréquentes, et un lien vers la leçon et les exercices.</p>
      </header>
      {themes?.map(t => (
        <article key={`${t.subject}/${t.slug}`} className="box">
          <p className="small muted">{subjectTitle[t.subject] ?? t.subject}</p>
          <h2>{t.title}</h2>
          <div className="wiki-cards">
            {t.pages.map(p => <Card key={p.path} page={p} />)}
          </div>
        </article>
      ))}
    </section>
  );
}

function Card({ page }: { page: WikiBrief }) {
  return <Link className="wiki-card" to={`/wiki/${page.path}`}><strong>{page.title}</strong><span>{page.summary}</span></Link>;
}

function PageView({ path, subjectTitle, unitTitle }: {
  path: string; subjectTitle: Record<string, string>; unitTitle: Record<string, string>;
}) {
  const [page, setPage] = useState<Page | null>(null);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.wikiPage(path).then(p => {
      setPage(p);
      // widgets inside a page need the unit they belong to (its items, its language)
      if (p.units[0]) api.unit(p.units[0]).then(setUnit).catch(() => setUnit(null));
    }).catch(e => setError(e instanceof ApiError ? e.message : "Erreur réseau."));
  }, [path]);

  const html = useMemo(() => (page ? marked.parse(page.body, { async: false }) : ""), [page]);
  if (error) return <p className="feedback no">{error} <Link to="/wiki">Toutes les fiches</Link></p>;
  if (!page) return <p className="muted">Chargement…</p>;

  return (
    <article className="wrap">
      <header className="intro">
        <p className="small muted"><Link to="/wiki">Fiches</Link> › {subjectTitle[page.subject] ?? page.subject} › {page.theme_title}</p>
        <h1>{page.title}</h1>
        <p>{page.summary}</p>
        {page.objectives.length > 0 && <div className="chips">{page.objectives.map(o => <span key={o} className="pill">{o}</span>)}</div>}
      </header>
      <div className="box md wiki-body"><HtmlContent html={html} unit={unit} /></div>
      {(page.lessons.length > 0 || page.units.length > 0) && (
        <div className="box">
          <h2>S'entraîner</h2>
          <div className="chips">
            {page.lessons.map(l => {
              const [u, lesson] = l.split("/");
              return <Link key={l} className="btn ghost" to={`/u/${u}/${lesson}`}>Leçon : {unitTitle[u] ?? u}</Link>;
            })}
            {page.units.map(u => <Link key={u} className="btn" to={`/u/${u}/exercices`}>Exercices : {unitTitle[u] ?? u}</Link>)}
          </div>
        </div>
      )}
      {page.related.length > 0 && (
        <div className="box">
          <h2>Voir aussi</h2>
          <div className="wiki-cards">{page.related.map(r => <Card key={r.path} page={r} />)}</div>
        </div>
      )}
      {page.sources.length > 0 && (
        <p className="wiki-note">Sources : {page.sources.join(" · ")}</p>
      )}
    </article>
  );
}
