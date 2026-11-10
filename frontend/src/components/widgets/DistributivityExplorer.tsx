import { useId, useState } from "react";

/** Rectangle (a + b) × (c + d) cut in 4 parts: the area model of the double distributivity. */
export function DistributivityExplorer() {
  const [v, setV] = useState({ a: 5, b: 2, c: 4, d: 3 });
  const id = useId().replace(/:/g, "");
  const { a, b, c, d } = v;
  const W = a + b, H = c + d, pad = 0.4;
  const parts = [
    { x: 0, y: 0, w: a, h: c, cls: "sq-a", txt: `${a}·${c}` },
    { x: a, y: 0, w: b, h: c, cls: "sq-b", txt: `${b}·${c}` },
    { x: 0, y: c, w: a, h: d, cls: "sq-b", txt: `${a}·${d}` },
    { x: a, y: c, w: b, h: d, cls: "sq-c", txt: `${b}·${d}` },
  ];
  const fs = Math.max(W, H) * 0.075;
  const slider = (k: keyof typeof v, label: string) => (
    <>
      <label htmlFor={id + k}>{label} = <output>{v[k]}</output></label>
      <input type="range" id={id + k} min={1} max={8} step={1} value={v[k]}
        onChange={e => setV({ ...v, [k]: +e.target.value })} />
    </>
  );

  return (
    <div className="explo">
      <div className="ctrls">
        {slider("a", "a")}{slider("b", "b")}{slider("c", "c")}{slider("d", "d")}
        <div className="calc">
          ({a} + {b})({c} + {d}) = {W} · {H} = <strong>{W * H}</strong><br />
          {a}·{c} + {a}·{d} + {b}·{c} + {b}·{d}<br />
          = {a * c} + {a * d} + {b * c} + {b * d} = <strong>{a * c + a * d + b * c + b * d}</strong>
        </div>
        <p className="muted" style={{ fontSize: ".88rem" }}>Remplace a et c par x : (x + 2)(x + 3) = x² + 3x + 2x + 6.</p>
      </div>
      <svg viewBox={`${-pad - fs} ${-pad - fs} ${W + 2 * pad + fs} ${H + 2 * pad + fs}`}
        role="img" aria-label="Rectangle découpé en quatre parties">
        {parts.map((p, i) => (
          <g key={i}>
            <rect x={p.x} y={p.y} width={p.w} height={p.h} className={p.cls} />
            <text x={p.x + p.w / 2} y={p.y + p.h / 2} fontSize={Math.min(fs, p.w / 3, p.h / 1.6)} className="ex-lab">{p.txt}</text>
          </g>
        ))}
        <text x={a / 2} y={-fs * 0.6} fontSize={fs} className="ex-lab">a = {a}</text>
        <text x={a + b / 2} y={-fs * 0.6} fontSize={fs} className="ex-lab">b = {b}</text>
        <text x={-fs * 0.6} y={c / 2} fontSize={fs} className="ex-lab" transform={`rotate(-90 ${-fs * 0.6} ${c / 2})`}>c = {c}</text>
        <text x={-fs * 0.6} y={c + d / 2} fontSize={fs} className="ex-lab" transform={`rotate(-90 ${-fs * 0.6} ${c + d / 2})`}>d = {d}</text>
      </svg>
    </div>
  );
}
