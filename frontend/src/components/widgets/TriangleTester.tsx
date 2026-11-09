import { useState } from "react";
import { fr, parseNum, roundTo, sq } from "../../format";

/** Applies the converse of Pythagoras to three lengths typed by the student. */
export function TriangleTester() {
  const [vals, setVals] = useState(["9", "12", "15"]);
  const v = vals.map(parseNum);

  let content: JSX.Element | string;
  let ok = false;
  if (v.some(x => !(x > 0))) {
    content = "Entre trois longueurs positives.";
  } else {
    const [a, b, c] = [...v].sort((x, y) => x - y);
    if (a + b <= c) {
      content = `${fr(a)} + ${fr(b)} ≤ ${fr(c)} : ce triangle ne peut pas exister.`;
    } else {
      const c2 = sq(c), ab = roundTo(sq(a) + sq(b), 4);
      ok = Math.abs(c2 - ab) < 1e-6;
      content = (
        <>
          Plus long côté : {fr(c)}, donc {fr(c)}² = {fr(c2)}<br />
          {fr(a)}² + {fr(b)}² = {fr(sq(a))} + {fr(sq(b))} = {fr(ab)}<br />
          <strong>
            {ok ? "Égalité : le triangle est rectangle ✔"
              : c2 < ab ? "c² < a² + b² : pas rectangle (acutangle)" : "c² > a² + b² : pas rectangle (obtusangle)"}
          </strong>
        </>
      );
    }
  }

  return (
    <>
      <div className="tester">
        {vals.map((x, i) => (
          <input key={i} id={`t${i + 1}`} inputMode="decimal" value={x} aria-label={`Longueur ${i + 1}`}
            onChange={e => setVals(vals.map((y, j) => (j === i ? e.target.value : y)))} />
        ))}
      </div>
      <div className={`result${ok ? " ok" : ""}`}>{content}</div>
    </>
  );
}
