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
    maths-pythagore/
      unit.yaml                    title, levels, lessons, exercise types, mission, scoring
      theorie.html                 a lesson block (HTML with widget placeholders)
      vrai-faux.yaml               items: {kind: vf, items: [...]}
      erreurs.yaml                 items: {kind: error, items: [...]}
    anglais-metiers/
      unit.yaml
      vocab.yaml                   items: {kind: vocab, items: [...]}
```

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

**Only static content** (vocabulary, true/false, find the mistake): create `content/units/<slug>/unit.yaml` and its item files. Reuse existing generators (`common.true_false`, `common.find_mistake`, `vocab.*`). No code needed.

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

Answer kinds: `number` (with `tol` and `unit`), `choice` (index in `choices`), `side` (click on a side of a right-triangle figure), `text` (list of accepted spellings).
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
