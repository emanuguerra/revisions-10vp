// Mirrors backend/app/schemas.py

export interface UnitBrief { slug: string; title: string; subtitle: string; ui_lang: string; enabled: boolean }
export interface Subject { slug: string; title: string; color: string; planned: string[]; units: UnitBrief[] }

export type Block =
  | { type: "html"; content: string }
  | { type: "markdown"; content?: string; text?: string }
  | { type: "widget"; widget: string; props?: Record<string, unknown> };

export interface Lesson { slug: string; title: string; blocks: Block[] }

export interface Scoring { first: number; retry: number; hint_cost: number; streak_bonus: number; streak_from: number }

export interface UnitConfig {
  levels?: { label: string; info: string }[];
  categories?: Record<string, string>;
  mission?: {
    mode: "sequence" | "mix";
    counts?: number[];
    filter?: string;
    review_mistakes?: boolean;
    score_display?: "points" | "fraction";
    title?: string;
    description?: string;
    badges?: string[];
  };
  scoring?: Partial<Scoring>;
  training?: boolean;
  exercises_title?: string;
  speech_lang?: string;          // voice for pronunciation, e.g. "de-DE" (default English)
  break_videos?: BreakVideo[];   // suggested during focus breaks
  subtitle_fr?: string;
}

export interface Unit {
  slug: string; title: string; subtitle: string; ui_lang: "fr" | "en"; subject: string;
  config: UnitConfig; lessons: Lesson[]; exercises: { key: string; title: string }[];
}

export interface Item<T = Record<string, unknown>> { key: string; kind: string; data: T }

export interface VocabData {
  category: string; en: string; alt?: string[]; fr: string; pic: string; definition: string; example: string;
}

export interface WortData {
  category: string; de: string; art?: "der" | "die" | "das"; pl?: string; plural_only?: boolean;
  singular_only?: boolean; forms?: string; opposite?: string; known?: boolean; plus?: boolean;
  fr: string; pic: string; group?: string; example: string; example_fr: string;
}

export interface Profile { nickname: string; class_code: string; token: string; created_at: string }

export interface UnitProgress {
  unit: string; title: string; answered: number; correct_first: number; correct: number;
  best: Record<string, number>; missions_done: number; last_activity: string | null;
}

export interface TriangleFig {
  type: "right-triangle"; a: number; b: number; names: string; rot?: number; flip?: boolean;
  lab?: Partial<Record<Side, string>>; click?: boolean;
}
export interface ClimographFig {
  type: "climograph"; name: string; lat: number; alt: number; temp: number[]; prec: number[]; hide_name?: boolean;
}
export interface ForcesFig {
  type: "forces"; w: number; h: number; scale: number;
  forces: { x: number; y: number; dx: number; dy: number; label: string; color?: string }[];
}
export type Figure = TriangleFig | ClimographFig | ForcesFig;
export type Side = "a" | "b" | "c";

export interface Question {
  id: string; exercise: string; level: number; kind: "number" | "choice" | "side" | "text";
  category: string; prompt: string; choices: string[] | null; unit: string; figure: Figure | null;
  has_hint: boolean; hint: string | null; max_tries: number; tries: number;
  eliminated: (number | string)[]; status: "open" | "correct" | "wrong"; position: number | null;
  answers: string[];               // the student's checked answers, in order
  result: AnswerResult | null;     // correction, once the question is finished
}

export interface MissionState {
  id: number; unit: string; level: number; index: number; total: number; score: number;
  streak: number; good: number; good_first: number; status: string;
  mode: "mission" | "training"; exercise: string | null; answered: number;
}

export interface AnswerResult {
  status: "correct" | "retry" | "wrong" | "invalid"; message: string; final: boolean;
  tries: number; max_tries: number; eliminated: (number | string)[]; points: number;
  explain?: string; correct_answer?: number | string | null; answer_display?: string | null;
  summary?: string | null; speak?: string | null; mission?: MissionState | null;
}

export interface Mistake { item_key: string | null; summary: string | null; given: string | null; category: string }

export interface MissionFull { mission: MissionState; questions: Question[] }

export interface MissionNext {
  mission: MissionState; question: Question | null; best?: number | null; previous_best?: number | null; mistakes: Mistake[];
}

/** A video for the break: a YouTube link (shown in the page) or a search on YouTube. */
export interface BreakVideo { title: string; url?: string; search?: string }

export interface Badge {
  id: string; icon: string; title: string; description: string; goal: number; value: number; earned: boolean;
}

export interface Rewards {
  xp: number; level: number; level_title: string; level_start: number; next_level: number;
  stats: Record<string, number>; badges: Badge[];
}
