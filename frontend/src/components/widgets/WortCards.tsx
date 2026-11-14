import { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import { norm } from "../../format";
import { say, sayLabel, translateLink } from "../../speech";
import type { Item, Unit, WortData } from "../../types";

export const fullWord = (j: WortData) => (j.art ? `${j.art} ${j.de}` : j.de);

/** The word, with its article coloured like the lesson: der blue, die red, das green. */
export function Word({ j }: { j: WortData }) {
  return j.art
    ? <span lang="de"><span className={`art-${j.art}`}>{j.art}</span> {j.de}</span>
    : <span lang="de">{j.de}</span>;
}

/** The book's boxes: grey "Das kennst du schon", blue extra vocabulary. */
function Level({ j }: { j: WortData }) {
  if (j.known) return <span className="lvl known" title="Das kennst du schon">déjà vu</span>;
  if (j.plus) return <span className="lvl plus" title="Vocabulaire en plus">+ en plus</span>;
  return null;
}

/** Which language is on the front of the cards; the back always shows the German word in full. */
type Side = "de" | "fr";
const SIDE_KEY = "r10-wort-side";

function loadSide(): Side {
  try { return localStorage.getItem(SIDE_KEY) === "fr" ? "fr" : "de"; } catch { return "de"; }
}

function Card({ it, cat, lang, opposite, side }: {
  it: Item<WortData>; cat: string; lang: string; opposite?: WortData; side: Side;
}) {
  const [flipped, setFlipped] = useState(false);
  const [label, setLabel] = useState("🔊 Écouter");
  const [labelFr, setLabelFr] = useState("🔊 FR");
  const j = it.data;
  const toggle = () => setFlipped(f => !f);

  return (
    <div className={`card${flipped ? " flipped" : ""}`} role="button" tabIndex={0}
      aria-label={flipped ? fullWord(j) : side === "fr" ? j.fr : fullWord(j)}
      onClick={toggle}
      onKeyDown={e => { if ((e.key === "Enter" || e.key === " ") && e.target === e.currentTarget) { e.preventDefault(); toggle(); } }}>
      <div className="inner">
        <div className="face front">
          <span className="pic" aria-hidden="true">{j.pic}</span>
          {side === "fr"
            ? <span className="word" lang="fr">{j.fr}</span>
            : <span className="word"><Word j={j} /></span>}
          <span className="cat">{cat}</span>
          <Level j={j} />
        </div>
        <div className="face back">
          <span className="word"><Word j={j} /></span>
          <span className="fr">FR : {j.fr}</span>
          {j.pl && <p className="ex" style={{ fontStyle: "normal" }}>Pluriel : <span lang="de">die {j.pl}</span></p>}
          {j.plural_only && <p className="ex" style={{ fontStyle: "normal" }}>Seulement au pluriel</p>}
          {j.singular_only && <p className="ex" style={{ fontStyle: "normal" }}>Seulement au singulier</p>}
          {j.forms && <p className="ex" style={{ fontStyle: "normal" }} lang="de">{j.forms}</p>}
          {opposite && <p className="ex" style={{ fontStyle: "normal" }}>≠ <Word j={opposite} /></p>}
          <p className="ex" lang="de">« {j.example} »</p>
          <p className="ex" style={{ fontStyle: "normal" }}>{j.example_fr}</p>
          <div className="audio">
            <button className="speak" onClick={e => {
              e.stopPropagation();
              setLabel("🔊 Lecture…");
              say(`${fullWord(j)}. ${j.example}`, lang).then(r => setLabel(sayLabel(r, lang, "🔊 Écouter")));
            }}>{label}</button>
            <button className="speak" title="Écouter en français" onClick={e => {
              e.stopPropagation();
              setLabelFr("🔊 …");
              say(`${j.fr}. ${j.example_fr}`, "fr-FR").then(r => setLabelFr(r === "ok" ? "🔊 FR" : sayLabel(r, "fr-FR", "🔊 FR")));
            }}>{labelFr}</button>
            <a className="alt" href={translateLink(fullWord(j), lang)} target="_blank" rel="noopener" onClick={e => e.stopPropagation()}>Google Traduction ↗</a>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Flip cards for German words (items of kind "wort"), with a topic filter and a search. */
export function WortCards({ unit, kind = "wort" }: { unit: Unit; kind?: string }) {
  const [items, setItems] = useState<Item<WortData>[] | null>(null);
  const [cat, setCat] = useState("all");
  const [q, setQ] = useState("");
  const [side, setSide] = useState<Side>(loadSide);
  const chooseSide = (s: Side) => { setSide(s); try { localStorage.setItem(SIDE_KEY, s); } catch { /* private mode */ } };
  const cats = unit.config.categories ?? {};
  const lang = unit.config.speech_lang ?? "de-DE";

  useEffect(() => { api.items<WortData>(unit.slug, kind).then(setItems); }, [unit.slug, kind]);

  const list = useMemo(() => {
    const f = norm(q);
    return (items ?? []).filter(({ data: j }) => (cat === "all" || j.category === cat) &&
      (!f || norm(fullWord(j)).includes(f) || norm(j.fr).includes(f)));
  }, [items, cat, q]);

  const opposites = useMemo(() => {
    const byKey = new Map((items ?? []).map(i => [i.key, i.data]));
    const m = new Map<string, WortData>();
    for (const i of items ?? []) {
      const o = i.data.opposite && byKey.get(i.data.opposite);
      if (o) { m.set(i.key, o); m.set(i.data.opposite!, i.data); }
    }
    return m;
  }, [items]);

  if (!items) return <p className="muted">Chargement…</p>;
  const count = (c: string) => (c === "all" ? items.length : items.filter(i => i.data.category === c).length);

  return (
    <div className="wrap" style={{ gap: 16 }}>
      <div className="chips" aria-label="Thèmes">
        {["all", ...Object.keys(cats)].map(c => (
          <button key={c} className="chip" aria-pressed={c === cat} onClick={() => setCat(c)}>
            {c === "all" ? "Tous les mots" : cats[c]}<span className="n">{count(c)}</span>
          </button>
        ))}
      </div>
      <div className="chips" role="group" aria-label="Sens des cartes">
        <span className="muted" style={{ alignSelf: "center" }}>Recto des cartes :</span>
        <button className="chip" aria-pressed={side === "de"} onClick={() => chooseSide("de")}>🇩🇪 Allemand → français</button>
        <button className="chip" aria-pressed={side === "fr"} onClick={() => chooseSide("fr")}>🇫🇷 Français → allemand</button>
      </div>
      <div className="tools">
        <input id="search" type="search" value={q} onChange={e => setQ(e.target.value)}
          placeholder="Chercher un mot (allemand ou français)…" aria-label="Chercher" />
        <span className="hint">
          {side === "fr" ? "Trouve le mot allemand, puis retourne la carte ·" : "Clique sur une carte pour la retourner ·"} <span className="art-der">der</span> <span className="art-die">die</span> <span className="art-das">das</span>
        </span>
      </div>
      <div className="grid">
        {list.map(it => <Card key={`${side}-${it.key}`} it={it} cat={cats[it.data.category] ?? ""} lang={lang}
          opposite={opposites.get(it.key)} side={side} />)}
        {list.length === 0 && <p>Aucun mot trouvé.</p>}
      </div>
    </div>
  );
}
