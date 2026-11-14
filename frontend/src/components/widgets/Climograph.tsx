import { fr } from "../../format";

const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
const SCALES = [2, 5, 10, 20];   // mm of precipitation for 1 °C

export interface ClimographProps {
  name: string; lat: number; alt: number; temp: number[]; prec: number[]; hide_name?: boolean;
}

/**
 * Climate diagram: precipitation bars (right axis, mm) and the temperature curve (left axis, °C).
 * The precipitation scale (k mm for 1 °C) is the smallest that fits the wettest month, so dry and
 * wet climates both stay readable; Mumbai's monsoon months are cut and show their value.
 */
export function Climograph({ name, lat, alt, temp, prec, hide_name }: ClimographProps) {
  const tMin = Math.min(0, Math.floor(Math.min(...temp) / 10) * 10);
  const tMax = Math.max(30, Math.ceil(Math.max(...temp) / 10) * 10);
  const k = SCALES.find(s => s * tMax >= Math.max(...prec)) ?? SCALES[SCALES.length - 1];
  const W = 360, H = 250, L = 38, R = 322, T = 34, B = 220;
  const y = (t: number) => B - ((t - tMin) / (tMax - tMin)) * (B - T);
  const x = (i: number) => L + ((i + 0.5) * (R - L)) / 12;
  const bw = ((R - L) / 12) * 0.7;
  const ticks: number[] = [];
  for (let t = tMin; t <= tMax; t += 10) ticks.push(t);
  const title = hide_name ? "Station mystère" : name;
  const sub = `${fr(Math.abs(lat))}° ${lat >= 0 ? "N" : "S"} · ${alt} m`;
  const total = prec.reduce((a, b) => a + b, 0);
  const mean = temp.reduce((a, b) => a + b, 0) / 12;

  return (
    <figure className="climograph">
      <svg viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label={`Diagramme climatique de ${title} : températures de ${fr(Math.min(...temp))} à ${fr(Math.max(...temp))} °C, ${total} mm de précipitations par an`}>
        <text x={W / 2} y={14} textAnchor="middle" className="cg-title">{title}</text>
        <text x={W / 2} y={27} textAnchor="middle" className="cg-sub">{sub}</text>
        {ticks.map(t => (
          <g key={t}>
            <line x1={L} x2={R} y1={y(t)} y2={y(t)} className={t === 0 ? "cg-zero" : "cg-grid"} />
            <text x={L - 4} y={y(t) + 3} textAnchor="end" className="cg-t">{t}</text>
            {t >= 0 && <text x={R + 4} y={y(t) + 3} className="cg-p">{t * k}</text>}
          </g>
        ))}
        <text x={L - 4} y={T - 6} textAnchor="end" className="cg-t">°C</text>
        <text x={R + 4} y={T - 6} className="cg-p">mm</text>
        {prec.map((p, i) => {
          const top = Math.max(y(p / k), T);
          return (
            <g key={i}>
              <rect x={x(i) - bw / 2} y={top} width={bw} height={Math.max(0, y(0) - top)} className="cg-bar" />
              {p / k > tMax && <text x={x(i)} y={T + 9} textAnchor="middle" className="cg-cut">{p}</text>}
            </g>
          );
        })}
        <polyline points={temp.map((t, i) => `${x(i)},${y(t)}`).join(" ")} className="cg-line" />
        {temp.map((t, i) => <circle key={i} cx={x(i)} cy={y(t)} r={2.5} className="cg-dot" />)}
        {MONTHS.map((m, i) => <text key={i} x={x(i)} y={B + 13} textAnchor="middle" className="cg-m">{m}</text>)}
      </svg>
      {!hide_name && (
        <figcaption className="muted">Moyenne annuelle {fr(Math.round(mean * 10) / 10)} °C · {total} mm par an</figcaption>
      )}
    </figure>
  );
}
