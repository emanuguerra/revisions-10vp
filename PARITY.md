# Parity with the original page (`jobs-vocabulary.html`)

Every feature of the single-page version, and where it lives now.

## English: jobs vocabulary
- [x] 92 jobs, 10 topics, Swiss French translations, alternative forms: `content/units/anglais-metiers/vocab.yaml` (extracted by script, not retyped)
- [x] Topic chips with counts, search (English, French, alternative forms), flip cards: `widgets/VocabCards.tsx`
- [x] 🔊 Listen (British voice first, Chrome cancel/speak workaround), Google Translate link, "Test sound": `speech.ts`, `widgets/SoundCheck.tsx`
- [x] Quiz with 5 question types (definition, translation, picture, gap-fill, spelling): `generators/vocab.py`
- [x] Distractors from the same topic first; every word asked once per quiz
- [x] 10 / 20 / 30 questions, topic filter
- [x] Spelling accepts the alternative forms (waitress, truck driver...)
- [x] Correction after a mistake: 3 attempts for spelling, 2 for multiple choice, "Show the answer"
- [x] Only a correct first answer counts; corrected words stay in "Words to review"
- [x] Result, words to review with the first wrong answer, "Practise my mistakes"
- [x] Word pronounced after each answer

## Maths: Pythagoras
- [x] Theory: vocabulary, theorem, two formulas, worked examples, converse with the 4 steps and a model sentence, acute/obtuse, "theorem or converse?" table, triplets, Egyptian rope, pitfalls: `content/units/maths-pythagore/theorie.html`
- [x] Figures: `widgets/TriangleFigure.tsx` (same drawing code as before)
- [x] Explorer with the three squares and unit grid: `widgets/PythagoreExplorer.tsx`
- [x] Triangle tester: `widgets/TriangleTester.tsx`
- [x] 8 exercise types × 3 levels: `generators/pythagore.py`, `generators/common.py`
- [x] Mission of 10 questions in the same order, free training per exercise type
- [x] Scoring: 10 / 5 after correction / hint −3 / streak +5 from 3 first-try answers in a row
- [x] Corrections: 3 attempts for numbers, "close: check the rounding" message, wrong options eliminated, true/false reveals after one mistake, hypotenuse: 2 wrong sides then the correction
- [x] Stars, badges, record per level (now saved in the database instead of the browser)
- [x] Swiss number formatting (1 440 000, 8,6) and comma input

## Changed on purpose
- Answers are checked by the server; the browser does not know the answer before the end.
- The English quiz result counts correct first answers ("8 / 10"), as before; the score is stored with the mission.
- Progress and records are tied to a student profile, not to one browser.
