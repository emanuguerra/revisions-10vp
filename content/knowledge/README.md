# Base de connaissance

Une fiche Markdown par notion : `<matière>/<thème>/<fiche>.md`, avec un en-tête YAML
(voir `backend/app/knowledge.py`). Les fiches sont écrites avec nos propres mots à partir
des sources citées : on ne recopie pas les manuels ni les épreuves officielles.

Elles servent à écrire les leçons et les exercices de l'app, et seront la base des réponses du chat.
Lien vers une autre fiche : `[albédo](wiki:geographie/climat/albedo)`.
Widget de l'app : `<div data-widget="albedo-explorer"></div>` (affiché avec l'unité citée dans `units`).

Vérifier après chaque modification : `cd backend && uv run python -m app.seed --check`.
