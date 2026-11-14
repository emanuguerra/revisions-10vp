import { useEffect, useState } from "react";
import { api } from "../../api";
import { speak } from "../../speech";
import type { Item, Unit, WortData } from "../../types";
import { fullWord, Word } from "./WortCards";

interface Tile { id: string; key: string; side: "de" | "fr"; it: WortData }

const shuffle = <T,>(a: T[]) => {
  const b = [...a];
  for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; }
  return b;
};

/** Memory: turn two tiles, find each German word and its French meaning. */
export function MemoryGame({ unit, kind = "wort", pairs = 6 }: { unit: Unit; kind?: string; pairs?: number }) {
  const [items, setItems] = useState<Item<WortData>[] | null>(null);
  const [cat, setCat] = useState("all");
  const [tiles, setTiles] = useState<Tile[]>([]);
  const [open, setOpen] = useState<string[]>([]);
  const [found, setFound] = useState<Set<string>>(new Set());
  const [moves, setMoves] = useState(0);
  const cats = unit.config.categories ?? {};
  const lang = unit.config.speech_lang ?? "de-DE";

  useEffect(() => { api.items<WortData>(unit.slug, kind).then(setItems); }, [unit.slug, kind]);

  function deal(c = cat) {
    if (!items) return;
    const pool = items.filter(i => c === "all" || i.data.category === c);
    // Two words with the same or a close French meaning would make the game ambiguous
    const seen = new Set<string>();
    const chosen = shuffle(pool).filter(i => {
      const ids = [i.data.fr, i.data.group ?? i.key];
      if (ids.some(x => seen.has(x))) return false;
      ids.forEach(x => seen.add(x));
      return true;
    }).slice(0, pairs);
    setTiles(shuffle(chosen.flatMap(i => [
      { id: i.key + ":de", key: i.key, side: "de" as const, it: i.data },
      { id: i.key + ":fr", key: i.key, side: "fr" as const, it: i.data },
    ])));
    setOpen([]); setFound(new Set()); setMoves(0);
  }

  useEffect(() => { deal(); }, [items]);  // eslint-disable-line react-hooks/exhaustive-deps

  function flip(t: Tile) {
    if (found.has(t.key) || open.includes(t.id) || open.length === 2) return;
    speak(t.side === "de" ? fullWord(t.it) : t.it.fr, t.side === "de" ? lang : "fr-FR");
    const next = [...open, t.id];
    setOpen(next);
    if (next.length < 2) return;
    setMoves(m => m + 1);
    const [a, b] = next.map(id => tiles.find(x => x.id === id)!);
    if (a.key === b.key) {
      setTimeout(() => { setFound(f => new Set(f).add(a.key)); setOpen([]); }, 400);
    } else {
      setTimeout(() => setOpen([]), 1100);
    }
  }

  if (!items) return <p className="muted">Chargement…</p>;
  const done = tiles.length > 0 && found.size * 2 === tiles.length;

  return (
    <div className="wrap" style={{ gap: 16 }}>
      <p>Retourne deux cartes : trouve le mot allemand et sa traduction. Chaque carte est lue quand tu la retournes : en allemand ou en français.</p>
      <div className="chips" aria-label="Thèmes">
        {["all", ...Object.keys(cats)].map(c => (
          <button key={c} className="chip" aria-pressed={c === cat} onClick={() => { setCat(c); deal(c); }}>
            {c === "all" ? "Tous les mots" : cats[c]}
          </button>
        ))}
      </div>
      <div className="memory-bar">
        <span>Paires : <strong>{found.size} / {tiles.length / 2}</strong> · Coups : <strong>{moves}</strong></span>
        <button className="btn small" onClick={() => deal()}>Nouvelle partie</button>
      </div>
      {done && (
        <p className="feedback ok">
          🎉 Bravo ! Toutes les paires en {moves} coups{moves <= tiles.length / 2 + 2 ? " : excellente mémoire !" : "."}
        </p>
      )}
      <div className="memory">
        {tiles.map(t => {
          const shown = open.includes(t.id) || found.has(t.key);
          return (
            <button key={t.id} className={`mtile${shown ? " shown" : ""}${found.has(t.key) ? " found" : ""}`}
              onClick={() => flip(t)} aria-label={shown ? (t.side === "de" ? fullWord(t.it) : t.it.fr) : "Carte cachée"}>
              {shown
                ? (t.side === "de"
                  ? <><span className="mpic" aria-hidden="true">{t.it.pic}</span><Word j={t.it} /></>
                  : <span lang="fr">{t.it.fr}</span>)
                : <span aria-hidden="true">?</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
