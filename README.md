# Révisions 10e

Revision app for the Swiss 10VP programme (10th year, *voie prégymnasiale*): theory pages, exercises and quizzes, with student progress saved in a database.

It started as a single HTML page (`../jobs-vocabulary.html`, kept as a reference). Everything in that page is now in this app; see [PARITY.md](PARITY.md).

- **frontend/**: React + TypeScript (Vite)
- **backend/**: Python, FastAPI, SQLAlchemy, Alembic. SQLite by default, Postgres through `DATABASE_URL`
- **content/**: the course material, as YAML/HTML files you edit without touching code

## Run it

You need [uv](https://docs.astral.sh/uv/) and Node 20 or later.

```bash
# API on http://localhost:8010
cd backend
uv sync
uv run alembic upgrade head      # create or upgrade the database (backend/data/app.db)
uv run python -m app.seed        # load content/ into the database
uv run uvicorn app.main:app --port 8010 --reload

# Web app on http://localhost:5180 (proxies /api to :8010)
cd frontend
npm install
npm run dev
```

With Docker: `docker compose up --build`, then open http://localhost:5180.

API documentation (Swagger) is at http://localhost:8010/docs.

## How content is organised

```
content/
  subjects.yaml                    branches (maths, français, anglais...) + planned topics ("Bientôt")
  units/
    maths-calcul-litteral/         same layout as maths-pythagore (generators: generators/litteral.py)
    maths-pythagore/
      unit.yaml                    title, levels, lessons, exercise types, mission, scoring
      theorie.html                 a lesson block (HTML with widget placeholders)
      vrai-faux.yaml               items: {kind: vf, items: [...]}
      erreurs.yaml                 items: {kind: error, items: [...]}
    anglais-metiers/
      unit.yaml
      vocab.yaml                   items: {kind: vocab, items: [...]}
    allemand-gefuehle/             German, Geni@l klick chapter 3 "Wie geht's denn so?" (generators/wort.py)
      unit.yaml                    speech_lang: de-DE gives a German voice to cards, Memory and answers
      woerter.yaml                 the book's word list: {kind: wort} de, art, pl, forms, opposite,
                                   known (grey box) / plus (blue box), fr, pic, group, example(+_fr)
      situationen.yaml             {kind: situation}: a short story, the missing word, 3 wrong words
      dialoge.yaml                 {kind: dialog}: what someone says, the right reply, 3 wrong replies
      wie-gehts.html               lesson
    allemand-kleidung/             chapter 4 "Kaufen, verkaufen, leihen", same layout, lektion.html
    phys-forces/                   physique MEP: forces (generators/forces.py, figure "forces" on squared paper)
    fr-vieille-dame/               français: La Visite de la vieille dame (common.mcq, common.order for the chronology)
    geo-climat/                    géographie, climate change (generators/climat.py + common.mcq)
      stations.yaml                {kind: station}: monthly temperatures and precipitation for the diagrams
      qcm.yaml, tri.yaml, documents.yaml   multiple choice ({question, answer, wrong, why}), sorting into
                                   fixed choices ({question, choices, answer, why}), documents ({doc, ...})
```

German words follow the book's word lists (categories = the parts of the list). `group` marks
near-synonyms (froh / glücklich) so one is never a wrong choice for the other; `opposite` feeds
the "Le contraire" exercise. Typed answers accept the word with or without its article, `ae/oe/ue` for `ä/ö/ü`, and `ss` for `ß`.

A **unit** is a chapter. It has:

- **lessons**: lists of blocks. A block is `html` (inline or `file:`), `markdown` (`text:` or `file:`), or `widget`.
  Inside HTML or Markdown, `<div data-widget="triangle-figure" data-props='{"a":4,"b":3}'></div>` mounts an interactive widget.
  The widgets are in `frontend/src/components/widgets/`.
- **exercises**: each one points to a **generator** (Python function) and optional `params`.
- **items**: static content (vocabulary, true/false statements, mistakes to find) used by the generators.
- **mission**: either a fixed `sequence` of exercises (maths) or a `mix` with a question count and a topic filter (vocabulary).
- **scoring**: points for a first try, after a correction, the cost of a hint, the streak bonus.

After any change in `content/`:

```bash
uv run python -m app.seed --check   # validate only
uv run python -m app.seed           # update the database (student history is kept)
```

## Add a chapter

**Only static content** (vocabulary, true/false, find the mistake): create `content/units/<slug>/unit.yaml` and its item files. Reuse existing generators (`common.true_false`, `common.find_mistake`, `vocab.*` for English, `wort.*` for German). No code needed.

**New kind of exercise** (for example solving linear equations):

1. Create `backend/app/generators/equations.py`:

   ```python
   from .base import GenContext, Generated, register

   @register("equations.linear")
   def linear(ctx: GenContext) -> Generated:
       a, x = ctx.rnd(2, 9), ctx.rnd(-10, 10)
       b = ctx.rnd(-20, 20)
       return Generated(
           kind="number", category=ctx.title, answer=x, tol=0.001,
           prompt=f"Résous : {a}x + {b} = {a * x + b}",
           hint="Isole x : soustrais d'abord, puis divise.",
           explain=f"{a}x = {a * x + b} − {b} = {a * x}<br>x = <strong>{x}</strong>",
       )
   ```

2. Import the module in `backend/app/generators/__init__.py`.
3. Reference it in a `unit.yaml`: `- {key: lin, title: Équations, generator: equations.linear}`.
4. Run `uv run pytest`. The generator tests run every exercise of every unit 200 times per level automatically.

Answer kinds: `number` (with `tol` and `unit`), `choice` (index in `choices`), `side` (click on a side of a right-triangle figure), `text` (list of accepted spellings; with `check="expr"` the answer is an algebraic expression compared by `app/algebra.py`: any equivalent expression in the requested `form` is accepted, e.g. `15 + 6x` for `6x + 15`).
The server checks answers, so the right answer is never sent to the browser before the end.

**New interactive widget**: add a component in `frontend/src/components/widgets/` and register it in `widgets/index.tsx`.

## Rules for answers and points

These live in `backend/app/engine.py`:

- A wrong answer can be corrected. `number` and `text` answers allow `max_tries` attempts (3 by default, set by the generator).
- `choice` and `side`: every wrong option is eliminated. If only the right option would be left (true/false, yes/no), the correction is shown, so the answer is not given away.
- "Voir la correction" ends the question with 0 points.
- Points come from the unit's `scoring`. Maths: 10 at the first try, 5 after a correction, minus 3 for a hint, +5 from the 3rd first-try answer in a row. Vocabulary: 1 point per correct first answer only.

## Students

Students create a profile with a nickname and an optional class code, without a password. The browser stores a token; the "Ma progression" page shows it as a **recovery code** for another device.
This is fine for revision at home or in class. Add real authentication before putting personal data on a public server.

## Put it online (Fly.io)

The root `Dockerfile` builds the frontend and serves it from the API: one small container.
SQLite lives on a Fly volume mounted at `/data`, so progress survives restarts and deployments.
With `ACCESS_CODE` set, the app asks for that code once per browser (profiles have no password).

```bash
fly volumes create data --region cdg --size 1     # once
fly secrets set ACCESS_CODE=choose-a-code         # once, or to change the code
fly deploy --ha=false                             # each update (--ha=false: one machine, SQLite)
fly logs                                          # if something goes wrong
```

The app is then at https://revisions-10vp.fly.dev. It sleeps when unused and wakes up in a few
seconds. Back up the database: `fly ssh sftp get /data/app.db`.

## Rewards and focus sessions

- **XP, levels and badges** are computed from the answers, missions and focus sessions
  (`backend/app/rewards.py`, `GET /api/profiles/me/rewards`): change the rules or add a badge
  there, past work counts too. A new badge or level shows a toast; all badges are on "Ma progression".
- **Focus sessions** (button "⏱️ Concentration"): 15 or 20 minutes, then a 5-minute break screen
  with an idea to move and videos on the chapter's theme. `break_videos` in unit.yaml lists them:
  `{title, search}` opens a YouTube search, `{title, url}` with a YouTube link plays in the page.
  A finished session is saved (`POST /api/profiles/me/focus`, table `focus_sessions`).

## Database

- Schema: `backend/app/models.py`. After changing it: `uv run alembic revision --autogenerate -m "..."`, then `uv run alembic upgrade head`.
- Postgres: `DATABASE_URL=postgresql+psycopg://user:password@host:5432/db`.

## Tests

```bash
cd backend && uv run pytest        # generators, formatting, API flows (missions, retries, scoring)
cd frontend && npm run build       # TypeScript check + production build
```

## Possible next steps

- A teacher page: progress of every student with the same class code
- Real accounts (teacher / student) if the app goes online
- More chapters from the 10VP plan: see the "Bientôt" topics in `content/subjects.yaml`, to check against the PER and your canton's teaching materials
