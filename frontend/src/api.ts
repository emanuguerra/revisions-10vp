import type {
  AnswerResult, Item, MissionFull, MissionNext, MissionState, Profile, Question, Rewards, Subject, Unit, UnitProgress,
} from "./types";

const TOKEN_KEY = "r10-token";
let memoryToken: string | null = null;

export function getToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY) ?? memoryToken; } catch { return memoryToken; }
}
export function setToken(token: string | null) {
  memoryToken = token;
  try { if (token) localStorage.setItem(TOKEN_KEY, token); else localStorage.removeItem(TOKEN_KEY); } catch { /* private mode */ }
}

// Shared access code of an online installation (ACCESS_CODE on the server), kept in this browser
const ACCESS_KEY = "r10-access";
export function getAccess(): string {
  try { return localStorage.getItem(ACCESS_KEY) ?? ""; } catch { return ""; }
}
export function setAccess(code: string) {
  try { localStorage.setItem(ACCESS_KEY, code); } catch { /* private mode */ }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-Profile-Token": token } : {}),
      ...(getAccess() ? { "X-Access-Code": getAccess() } : {}),
      ...init.headers,
    },
  });
  if (res.status === 403) window.dispatchEvent(new Event("r10-access-needed"));
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail ?? msg; } catch { /* not JSON */ }
    throw new ApiError(res.status, typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body?: unknown) =>
  call<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  access: () => call<{ required: boolean; ok: boolean }>("/access"),
  subjects: () => call<Subject[]>("/subjects"),
  unit: (slug: string) => call<Unit>(`/units/${slug}`),
  items: <T>(slug: string, kind?: string) => call<Item<T>[]>(`/units/${slug}/items${kind ? `?kind=${kind}` : ""}`),

  createProfile: (nickname: string, class_code: string) => post<Profile>("/profiles", { nickname, class_code }),
  me: () => call<Profile>("/profiles/me"),
  progress: (unit?: string) => call<UnitProgress[]>(`/profiles/me/progress${unit ? `?unit=${unit}` : ""}`),
  rewards: () => call<Rewards>("/profiles/me/rewards"),
  focusDone: (minutes: number) => call<Rewards>("/profiles/me/focus", { method: "POST", body: JSON.stringify({ minutes }) }),

  startMission: (body: { unit: string; level?: number; count?: number; category?: string | null; item_keys?: string[] }) =>
    post<{ mission: MissionState; question: Question }>("/missions", body),
  nextInMission: (id: number) => post<MissionNext>(`/missions/${id}/next`),
  abandonMission: (id: number) => post<MissionState>(`/missions/${id}/abandon`),
  // sessions left in the middle, and a whole session with its questions (resume, go back)
  activeSessions: (unit: string) => call<MissionState[]>(`/missions/active?unit=${unit}`),
  mission: (id: number) => call<MissionFull>(`/missions/${id}`),
  startTraining: (unit: string, exercise: string, level: number) =>
    post<{ mission: MissionState; question: Question }>("/training", { unit, exercise, level }),
  question: (id: string) => call<Question>(`/questions/${id}`),

  trainingQuestion: (unit: string, exercise: string, level: number) => post<Question>("/questions", { unit, exercise, level }),
  answer: (id: string, value: string | number) => post<AnswerResult>(`/questions/${id}/answer`, { value }),
  hint: (id: string) => post<{ hint: string }>(`/questions/${id}/hint`),
  reveal: (id: string) => post<AnswerResult>(`/questions/${id}/reveal`),
};
