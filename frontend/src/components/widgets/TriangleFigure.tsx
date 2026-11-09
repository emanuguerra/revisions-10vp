import type { Side } from "../../types";

/* Right triangle: names[2] = right-angle vertex R, names[1] = P (end of leg a), names[0] = Q (end of leg b).
   Side a = [RP], side b = [RQ], side c = [PQ] (hypotenuse). Same convention as backend/app/generators/pythagore.py. */
export interface TriangleProps {
  a: number;
  b: number;
  names?: string;
  lab?: Partial<Record<Side, string>>;
  rot?: number;
  flip?: boolean;
  click?: boolean;
  pad?: number;
  size?: number;
  sideState?: Partial<Record<Side, "ok" | "ko">>;
  onSide?: (side: Side) => void;
}

type Pt = [number, number];
const seg = (p: string, q: string) => [p, q].sort().join("");

export function TriangleFigure({
  a, b, names = "ABC", lab = {}, rot = 0, flip = false, click = false, pad = 34, size = 260, sideState = {}, onSide,
}: TriangleProps) {
  const s = 150 / Math.max(a, b), th = (rot * Math.PI) / 180, f = flip ? -1 : 1;
  const T = (x: number, y: number): Pt => [
    (x * Math.cos(th) - f * y * Math.sin(th)) * s,
    (x * Math.sin(th) + f * y * Math.cos(th)) * s,
  ];
  const R = T(0, 0), P = T(a, 0), Q = T(0, b);
  const G: Pt = [(R[0] + P[0] + Q[0]) / 3, (R[1] + P[1] + Q[1]) / 3];
  const out = (p: Pt, d: number): Pt => {
    const dx = p[0] - G[0], dy = p[1] - G[1], L = Math.hypot(dx, dy) || 1;
    return [p[0] + (dx / L) * d, p[1] + (dy / L) * d];
  };
  const mid = (p: Pt, q: Pt): Pt => [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
  const unit = (p: Pt, q: Pt): Pt => {
    const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
    return [(q[0] - p[0]) / L, (q[1] - p[1]) / L];
  };
  const u = unit(R, P), v = unit(R, Q), m = 13;
  const mark: Pt[] = [
    [R[0] + u[0] * m, R[1] + u[1] * m],
    [R[0] + (u[0] + v[0]) * m, R[1] + (u[1] + v[1]) * m],
    [R[0] + v[0] * m, R[1] + v[1] * m],
  ];
  const sides: [Side, Pt, Pt, string][] = [
    ["a", R, P, seg(names[2], names[1])],
    ["b", R, Q, seg(names[2], names[0])],
    ["c", P, Q, seg(names[0], names[1])],
  ];
  const verts: [Pt, string][] = [[Q, names[0]], [P, names[1]], [R, names[2]]];
  const labPos = sides.map(([, p, q]) => out(mid(p, q), 22));
  const pts = [R, P, Q, ...labPos, ...verts.map(([p]) => out(p, 18))];
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const x0 = Math.min(...xs) - pad, y0 = Math.min(...ys) - 24;
  const w = Math.max(...xs) - x0 + pad, h = Math.max(...ys) - y0 + 24;
  const P2 = (p: Pt) => p.map(n => n.toFixed(1)).join(",");

  return (
    <svg className="tri" viewBox={`${x0.toFixed(1)} ${y0.toFixed(1)} ${w.toFixed(1)} ${h.toFixed(1)}`}
      style={{ maxWidth: size }} role="img" aria-label={`Triangle rectangle en ${names[2]}`}>
      <polygon className="tri-fill" points={[R, P, Q].map(P2).join(" ")} />
      <polyline className="tri-mark" points={mark.map(P2).join(" ")} />
      {sides.map(([k, p, q, name], i) => {
        const line = { x1: p[0], y1: p[1], x2: q[0], y2: q[1] };
        return (
          <g key={k}>
            <line className={`side ${sideState[k] ?? ""}`} {...line} />
            {click && (
              <line className="hit" {...line} tabIndex={0} role="button" aria-label={`Côté [${name}]`}
                onClick={() => onSide?.(k)}
                onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSide?.(k); } }}>
                <title>[{name}]</title>
              </line>
            )}
            {lab[k] != null && (
              <text className={`slab${lab[k] === "?" ? " q" : ""}`} x={labPos[i][0]} y={labPos[i][1]}>{lab[k]}</text>
            )}
          </g>
        );
      })}
      {verts.map(([p, n]) => {
        const o = out(p, 16);
        return <text key={n} className="vlab" x={o[0]} y={o[1]}>{n}</text>;
      })}
    </svg>
  );
}
