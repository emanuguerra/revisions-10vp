// Same rules as backend/app/formatting.py

export const roundTo = (x: number, d: number) => Math.round(x * 10 ** d) / 10 ** d;
export const sq = (x: number) => roundTo(x * x, 4);
export const fr = (x: number) => roundTo(x, 4).toLocaleString("fr-CH", { maximumFractionDigits: 4 });
export const parseNum = (s: string) => parseFloat(String(s).trim().replace(",", ".").replace(/[\s'’]/g, ""));
export const norm = (s: string) => s.trim().toLowerCase().replace(/[-\s]+/g, " ");
