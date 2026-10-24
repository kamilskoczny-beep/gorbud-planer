# Planer GORBUD – instrukcje dla Claude'a w tym repozytorium

- Język: polski (kod i identyfikatory po angielsku, komentarze/UI/dokumentacja po polsku).
- Zasady projektowe użytkownika są w `docs/ZASADY_PROJEKTOWE.md` – każda nowa reguła od użytkownika trafia tam w tej samej turze
  (plus pamięć projektu i umiejętność `gorbud-meblowanie-rzutow`).
- Edytor (`web/src/legacy/page.js`) przepisujemy etapami na moduły TS wg `docs/ARCHITEKTURA.md`; nie dublować logiki – nowy
  moduł zastępuje fragment `page.js`.
- Przed commitem: `cd web && npm run build` (tsc + vite) oraz test dymny `node ../tests/run.mjs` (wymaga Playwright).
- Jednostki: mm, układ lokalny kondygnacji, y w górę (SVG odwraca). Zaokrąglenia do 10 mm. Format pliku: `docs/FORMAT_PROJEKTU.md`.
- Dane budynków w `projects/<slug>/` – nie nadpisywać układów użytkownika bez pytania; zmiany punktowe, z zachowaniem id elementów.
- Commity po polsku, krótkie, z opisem „co dla użytkownika” (nie „co w kodzie”).
