import { useEffect, useId, useState } from "react";
import { api } from "../../api";
import { fr } from "../../format";
import type { Item, Unit } from "../../types";
import { Climograph, type ClimographProps } from "./Climograph";

interface Station extends Omit<ClimographProps, "name"> { name: string; country: string; climate: string }

const CLIMATE_NAMES: Record<string, string> = {
  oceanique: "tempéré océanique", continental: "tempéré continental", mediterraneen: "méditerranéen",
  equatorial: "équatorial", "tropical-sec": "tropical à saison sèche", desertique: "désertique",
  polaire: "polaire", montagnard: "montagnard", transition: "tempéré de transition", subtropical: "subtropical humide",
};

function facts(s: Station) {
  const amp = Math.round((Math.max(...s.temp) - Math.min(...s.temp)) * 10) / 10;
  return `Climat ${CLIMATE_NAMES[s.climate] ?? s.climate} · amplitude ${fr(amp)} °C`;
}

/** Two climate diagrams side by side: Geneva and a station to choose. */
export function ClimographExplorer({ unit }: { unit: Unit }) {
  const [stations, setStations] = useState<Item<Station>[] | null>(null);
  const [key, setKey] = useState("moscou");
  const id = useId();

  useEffect(() => { api.items<Station>(unit.slug, "station").then(setStations); }, [unit.slug]);
  if (!stations) return <p className="muted">Chargement…</p>;
  const ref = stations.find(s => s.key === "geneve") ?? stations[0];
  const other = stations.find(s => s.key === key) ?? stations[1];
  const props = (s: Item<Station>) => ({ ...s.data, name: `${s.data.name} (${s.data.country})` });

  return (
    <div className="climo-explorer">
      <label htmlFor={id}>Comparer avec :</label>{" "}
      <select id={id} className="field" style={{ width: "auto" }} value={key} onChange={e => setKey(e.target.value)}>
        {stations.filter(s => s.key !== ref.key).map(s => <option key={s.key} value={s.key}>{s.data.name} ({s.data.country})</option>)}
      </select>
      <div className="climo-pair">
        <div><Climograph {...props(ref)} /><p className="small-note">{facts(ref.data)}</p></div>
        <div><Climograph {...props(other)} /><p className="small-note">{facts(other.data)}</p></div>
      </div>
    </div>
  );
}

const SURFACES = [
  { name: "Neige fraîche", a: 0.85, color: "#f4f8ff" },
  { name: "Banquise", a: 0.6, color: "#dbe9f6" },
  { name: "Désert", a: 0.35, color: "#e9cf8f" },
  { name: "Prairie", a: 0.25, color: "#8cc56b" },
  { name: "Forêt", a: 0.15, color: "#3f7d3a" },
  { name: "Océan", a: 0.06, color: "#1f4e79" },
];

/** Choose a surface and see how much of 340 W/m² it reflects and absorbs; then melt the sea ice. */
export function AlbedoExplorer() {
  const [i, setI] = useState(1);
  const [ice, setIce] = useState(100);
  const s = SURFACES[i];
  const E = 340;
  // Arctic sea: sea ice where frozen, ocean elsewhere
  const arcticA = (ice / 100) * 0.6 + (1 - ice / 100) * 0.06;
  const id = useId();
  return (
    <div className="albedo">
      <div className="chips">
        {SURFACES.map((x, k) => (
          <button key={x.name} className="chip" aria-pressed={k === i} onClick={() => setI(k)}>{x.name}</button>
        ))}
      </div>
      <div className="albedo-bar" aria-label={`${s.name} : albédo ${fr(s.a)}`}>
        <span className="refl" style={{ width: `${s.a * 100}%` }}>{s.a >= 0.2 ? `réfléchi ${fr(Math.round(E * s.a))} W/m²` : ""}</span>
        <span className="abs" style={{ width: `${(1 - s.a) * 100}%`, background: s.color }}>
          {s.a <= 0.8 ? `absorbé ${fr(Math.round(E * (1 - s.a)))} W/m²` : ""}
        </span>
      </div>
      <p className="small-note">{s.name} : albédo {fr(s.a)}. Sur {E} W/m² reçus, {fr(Math.round(E * s.a))} sont réfléchis et {fr(Math.round(E * (1 - s.a)))} absorbés.</p>
      <label htmlFor={id}>Banquise arctique en été : <output>{ice} %</output> de la surface</label>
      <input id={id} type="range" min={0} max={100} step={5} value={ice} onChange={e => setIce(+e.target.value)} />
      <p className="small-note">
        Albédo moyen de la région : <strong>{fr(Math.round(arcticA * 100) / 100)}</strong>. Énergie absorbée :{" "}
        <strong>{fr(Math.round(E * (1 - arcticA)))} W/m²</strong>
        {ice < 100 ? ` (+${fr(Math.round(E * (1 - arcticA)) - Math.round(E * 0.4))} W/m² par rapport à une banquise complète) : la région se réchauffe, la glace fond encore plus.` : "."}
      </p>
    </div>
  );
}
