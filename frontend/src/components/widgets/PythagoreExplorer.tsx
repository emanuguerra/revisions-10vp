import { useId, useState } from "react";
import { fr, roundTo, sq } from "../../format";

/** Right triangle with a square on each side; sliders change the legs. */
export function PythagoreExplorer() {
  const [a, setA] = useState(3);
  const [b, setB] = useState(4);
  const gridId = "grid" + useId().replace(/:/g, "");
  const c2 = roundTo(sq(a) + sq(b), 4), c = Math.sqrt(c2);
  const pts = (arr: number[][]) => arr.map(([x, y]) => `${x},${-y}`).join(" ");
  const A = [[0, 0], [a, 0], [a, -a], [0, -a]];
  const B = [[0, 0], [0, b], [-b, b], [-b, 0]];
  const C = [[a, 0], [0, b], [b, a + b], [a + b, a]];
  const pad = 0.6;
  const label = (x: number, y: number, side: number, txt: string) => (
    <text x={x} y={-y} fontSize={Math.min(side / 3.8, (a + b) * 0.09)} className="ex-lab">{txt}</text>
  );
  const exact = Math.abs(c - roundTo(c, 2)) < 1e-9;

  return (
    <div className="explo">
      <div className="ctrls">
        <label htmlFor="sa">Cathète a = <output>{fr(a)}</output></label>
        <input type="range" id="sa" min={1} max={10} step={0.5} value={a} onChange={e => setA(+e.target.value)} />
        <label htmlFor="sb">Cathète b = <output>{fr(b)}</output></label>
        <input type="range" id="sb" min={1} max={10} step={0.5} value={b} onChange={e => setB(+e.target.value)} />
        <div className="calc">
          a² + b² = c²<br />
          {fr(sq(a))} + {fr(sq(b))} = {fr(c2)}<br />
          c = √{fr(c2)} {exact ? "=" : "≈"} <strong>{fr(roundTo(c, 2))}</strong>
        </div>
        <p className="muted" style={{ fontSize: ".88rem" }}>Avec des nombres entiers, compte les petits carrés : 9 + 16 = 25.</p>
      </div>
      <svg viewBox={`${-b - pad} ${-(a + b) - pad} ${a + 2 * b + 2 * pad} ${2 * a + b + 2 * pad}`}
        role="img" aria-label="Triangle rectangle avec un carré construit sur chaque côté">
        <defs>
          <pattern id={gridId} width="1" height="1" patternUnits="userSpaceOnUse">
            <path d="M1 0H0V1" fill="none" className="grid-line" strokeWidth="0.03" />
          </pattern>
        </defs>
        <polygon points={pts(A)} className="sq-a" />
        <polygon points={pts(A)} fill={`url(#${gridId})`} />
        <polygon points={pts(B)} className="sq-b" />
        <polygon points={pts(B)} fill={`url(#${gridId})`} />
        <polygon points={pts(C)} className="sq-c" />
        <polygon points={pts([[0, 0], [a, 0], [0, b]])} className="ex-tri" />
        {label(a / 2, -a / 2, a, `a² = ${fr(sq(a))}`)}
        {label(-b / 2, b / 2, b, `b² = ${fr(sq(b))}`)}
        {label((a + b) / 2, (a + b) / 2, c, `c² = ${fr(c2)}`)}
      </svg>
    </div>
  );
}
