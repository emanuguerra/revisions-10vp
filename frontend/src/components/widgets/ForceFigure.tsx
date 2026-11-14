import { useId, useState } from "react";
import { fr } from "../../format";

export interface Arrow { x: number; y: number; dx: number; dy: number; label: string; color?: string }
export interface ForceFigureProps { w: number; h: number; scale: number; forces: Arrow[]; unitLabel?: string }

const C = 24;  // pixels per grid square

/** Forces drawn as arrows on squared paper, `scale` newtons per square (y grows downwards). */
export function ForceFigure({ w, h, scale, forces }: ForceFigureProps) {
  const id = useId().replace(/:/g, "");
  const lines = [];
  for (let i = 0; i <= w; i++) lines.push(<line key={`v${i}`} x1={i * C} y1={0} x2={i * C} y2={h * C} className="fg-grid" />);
  for (let j = 0; j <= h; j++) lines.push(<line key={`h${j}`} x1={0} y1={j * C} x2={w * C} y2={j * C} className="fg-grid" />);
  return (
    <figure className="forcefig">
      <svg viewBox={`-4 -4 ${w * C + 8} ${h * C + 8}`} role="img"
        aria-label={`Schéma de ${forces.length} force${forces.length > 1 ? "s" : ""} sur un quadrillage, 1 carré pour ${scale} N`}>
        <defs>
          {["f1", "f2", "r"].map(c => (
            <marker key={c} id={`${id}-${c}`} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" className={`fg-head ${c}`} />
            </marker>
          ))}
        </defs>
        {lines}
        {forces.map((f, i) => {
          const c = f.color ?? "f1";
          const x2 = (f.x + f.dx) * C, y2 = (f.y + f.dy) * C;
          const len = Math.hypot(f.dx, f.dy) || 1;
          // label beside the middle of the arrow, pushed sideways
          const mx = (f.x + f.dx / 2) * C - (f.dy / len) * 12, my = (f.y + f.dy / 2) * C + (f.dx / len) * 12 + 4;
          return (
            <g key={i}>
              <line x1={f.x * C} y1={f.y * C} x2={x2} y2={y2} className={`fg-arrow ${c}`} markerEnd={`url(#${id}-${c})`} />
              <circle cx={f.x * C} cy={f.y * C} r={3.5} className="fg-origin" />
              <text x={mx} y={my} textAnchor="middle" className={`fg-label ${c}`}>{f.label}</text>
            </g>
          );
        })}
      </svg>
      <figcaption className="muted">1 carré ↔ {fr(scale)} N</figcaption>
    </figure>
  );
}

/** Two forces on a point: change their intensity and angle, see the parallelogram and the resultant. */
export function ForceAdder() {
  const [f1, setF1] = useState(40);
  const [f2, setF2] = useState(30);
  const [deg, setDeg] = useState(90);
  const id = useId();
  const a = (deg * Math.PI) / 180;
  const rx = f1 + f2 * Math.cos(a), ry = f2 * Math.sin(a);
  const r = Math.hypot(rx, ry);
  const s = 10, ox = 7, oy = 8, w = 20, h = 10;
  const arrows: Arrow[] = [
    { x: ox, y: oy, dx: f1 / s, dy: 0, label: "F₁", color: "f1" },
    { x: ox, y: oy, dx: (f2 / s) * Math.cos(a), dy: -(f2 / s) * Math.sin(a), label: "F₂", color: "f2" },
    { x: ox, y: oy, dx: rx / s, dy: -ry / s, label: "R", color: "r" },
  ];
  const slider = (label: string, v: number, set: (n: number) => void, min: number, max: number, step: number, unit: string) => (
    <>
      <label htmlFor={id + label}>{label} = <output>{v} {unit}</output></label>
      <input id={id + label} type="range" min={min} max={max} step={step} value={v} onChange={e => set(+e.target.value)} />
    </>
  );
  return (
    <div className="explo">
      <div className="ctrls">
        {slider("F₁", f1, setF1, 0, 60, 5, "N")}
        {slider("F₂", f2, setF2, 0, 60, 5, "N")}
        {slider("Angle entre F₁ et F₂", deg, setDeg, 0, 180, 15, "°")}
        <div className="calc">
          Résultante R ≈ <strong>{fr(Math.round(r * 10) / 10)} N</strong>
          {deg === 90 && <><br />Pythagore : √({f1}² + {f2}²) = {fr(Math.round(r * 10) / 10)} N</>}
          {deg === 0 && <><br />Même sens : {f1} + {f2} = {f1 + f2} N</>}
          {deg === 180 && <><br />Sens contraires : |{f1} − {f2}| = {Math.abs(f1 - f2)} N</>}
          <br /><span className="muted">Force d'équilibre : {fr(Math.round(r * 10) / 10)} N, sens opposé à R.</span>
        </div>
      </div>
      <ForceFigure w={w} h={h} scale={s} forces={arrows} />
    </div>
  );
}
