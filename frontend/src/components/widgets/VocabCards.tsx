import { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import { norm } from "../../format";
import { say, sayLabel, translateLink } from "../../speech";
import type { Item, Unit, VocabData } from "../../types";

function Card({ it, cat }: { it: Item<VocabData>; cat: string }) {
  const [flipped, setFlipped] = useState(false);
  const [label, setLabel] = useState("🔊 Listen");
  const [labelFr, setLabelFr] = useState("🔊 FR");
  const j = it.data;
  const toggle = () => setFlipped(f => !f);

  return (
    <div className={`card${flipped ? " flipped" : ""}`} role="button" tabIndex={0} aria-label={j.en}
      onClick={toggle}
      onKeyDown={e => { if ((e.key === "Enter" || e.key === " ") && e.target === e.currentTarget) { e.preventDefault(); toggle(); } }}>
      <div className="inner">
        <div className="face front">
          <span className="pic" aria-hidden="true">{j.pic}</span>
          <span className="word">{j.en}</span>
          <span className="cat">{cat}</span>
        </div>
        <div className="face back">
          <span className="word">{j.en}</span>
          <span className="fr">FR: {j.fr}</span>
          <p>{j.definition}</p>
          {j.alt && <p className="ex" style={{ fontStyle: "normal" }}>Also: {j.alt.join(", ")}</p>}
          <p className="ex">“{j.example}”</p>
          <div className="audio">
            <button className="speak" onClick={e => {
              e.stopPropagation();
              setLabel("🔊 Playing…");
              say(j.en, "en-GB").then(r => setLabel(sayLabel(r, "en-GB", "🔊 Listen")));
            }}>{label}</button>
            <button className="speak" title="Écouter en français" onClick={e => {
              e.stopPropagation();
              setLabelFr("🔊 …");
              say(j.fr, "fr-FR").then(r => setLabelFr(r === "ok" ? "🔊 FR" : sayLabel(r, "fr-FR", "🔊 FR")));
            }}>{labelFr}</button>
            <a className="alt" href={translateLink(j.en)} target="_blank" rel="noopener" onClick={e => e.stopPropagation()}>Google Translate ↗</a>
          </div>
        </div>
      </div>
    </div>
  );
}

export function VocabCards({ unit, kind = "vocab" }: { unit: Unit; kind?: string }) {
  const [items, setItems] = useState<Item<VocabData>[] | null>(null);
  const [cat, setCat] = useState("all");
  const [q, setQ] = useState("");
  const cats = unit.config.categories ?? {};

  useEffect(() => { api.items<VocabData>(unit.slug, kind).then(setItems); }, [unit.slug, kind]);

  const list = useMemo(() => {
    const f = norm(q);
    return (items ?? []).filter(({ data: j }) => (cat === "all" || j.category === cat) &&
      (!f || norm(j.en).includes(f) || norm(j.fr).includes(f) || (j.alt ?? []).some(a => norm(a).includes(f))));
  }, [items, cat, q]);

  if (!items) return <p className="muted">Loading…</p>;
  const count = (c: string) => (c === "all" ? items.length : items.filter(i => i.data.category === c).length);

  return (
    <div className="wrap" style={{ gap: 16 }}>
      <div className="chips" aria-label="Topics">
        {["all", ...Object.keys(cats)].map(c => (
          <button key={c} className="chip" aria-pressed={c === cat} onClick={() => setCat(c)}>
            {c === "all" ? "All jobs" : cats[c]}<span className="n">{count(c)}</span>
          </button>
        ))}
      </div>
      <div className="tools">
        <input id="search" type="search" value={q} onChange={e => setQ(e.target.value)}
          placeholder="Search a job / Chercher un métier…" aria-label="Search" />
        <span className="hint">Click a card to flip it · Clique pour retourner</span>
      </div>
      <div className="grid">
        {list.map(it => <Card key={it.key} it={it} cat={cats[it.data.category] ?? ""} />)}
        {list.length === 0 && <p>No job found. / Aucun métier trouvé.</p>}
      </div>
    </div>
  );
}
