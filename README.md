# Planer GORBUD

Program do pracy nad układami funkcjonalnymi budynków (zmiana sposobu użytkowania, podział na mieszkania,
meblowanie) – rozwijany wspólnie przez GORBUD / SANDER i Claude'a. Wyrósł z modelu roboczego budynku
poczty przy ul. Pocztowej 11 w Drawsku Pomorskim i ma służyć w kolejnych projektach.

## Co już umie (etap 0 – przeniesiony model roboczy)
- Rzuty kondygnacji z inwentaryzacji DWG (ściany, okna, drzwi, schody, opisy, pomieszczenia z powierzchnią).
- Warianty koncepcji per kondygnacja, lokale (strefy, legenda z bilansem powierzchni).
- Ściany projektowane: tylko 90°, wybór strony grubości od linii, dowolna grubość, automatyczne łączenie (L, T),
  przesuwanie równoległe z dociąganiem, chwytanie końców (skracanie / wydłużanie do najbliższej ściany),
  edycja grubości z wyborem lica, „Wytnij” (usunięcie odcinka między ścianami poprzecznymi), wyburzenia.
- Drzwi jednym kliknięciem (80 cm, ościeżnica regulowana dopasowana do grubości ściany, skrzydło, 3 zawiasy,
  klamka), przesuwanie po ścianie, kierunek (R), zawias L/P (L), szerokość.
- Pomieszczenia: obrys liczony automatycznie ze ścian (flood fill), własny kolor, powierzchnia,
  na poddaszu powierzchnia użytkowa wg PN-ISO 9836 i zakres wysokości; osobne warstwy (kolor / obrys / etykieta).
- Meble (szafy = IKEA PAX 150/175/200/250/275/300), zakaz kolizji ze ścianami, dosuwanie do lica, pytanie co
  zrobić przy kolizji ściana–mebel.
- Wymiary automatyczne (pomieszczenia, przejścia, odległości przy przesuwaniu ścian).
- Skosy poddasza: linie załamania, h = 1,90 / 2,20, odczyt wysokości pod kursorem, połacie w 3D.
- Widok 3D (three.js): ściany, otwory, drzwi, meble, połacie; przesuwanie mebli i drzwi w 3D.
- Szkic, strzałki i numerowane uwagi „dla Claude’a” na rysunku.
- Wiele projektów w przeglądarce (IndexedDB), import/eksport pliku `.planer.json`.

Zasady projektowe (PAX, drzwi 80, kolizje, 90°, …) są spisane w `docs/ZASADY_PROJEKTOWE.md` i w umiejętności
`gorbud-meblowanie-rzutow` – każda nowa reguła trafia do obu.

## Uruchomienie
```bash
cd web
npm install
npm run dev        # http://localhost:5173
npm run build      # wersja produkcyjna w web/dist (statyczne pliki – można wrzucić na dowolny hosting)
npm test           # test dymny (Playwright): start, zapis, odczyt
```

## Nowy projekt z DWG
1. `tools/dwg` – `node dump.mjs plik.dwg > zsu.json` (parser WASM @mlightcad/libredwg-web), potem
   `python3 extract.py` i `python3 rooms.py` (parametry arkuszy w skrypcie) → `model.json`.
2. W aplikacji: **+ Nowy z model.json**.
3. Docelowo (etap 1) import DWG/DXF będzie wbudowany w aplikację (ten sam parser WASM w przeglądarce).

## Struktura
```
web/                 aplikacja (Vite + TypeScript)
  src/main.ts        powłoka: lista projektów, import/eksport, start edytora
  src/store.ts       magazyn projektów (IndexedDB)
  src/legacy/        edytor rzutów – kod przeniesiony z modelu roboczego (JS), przepisywany etapami
tools/dwg/           DWG → JSON (Node WASM + Python/OpenCV)
tools/               generator wariantów 108, łaty bazy, budowanie starej strony-artefaktu
projects/            dane projektów (Drawsko: model, warianty, układ 108, archiwum 13 wariantów)
docs/                architektura, format pliku projektu, zasady projektowe, mapa drogowa
tests/               testy dymne
```

## Mapa drogowa
Patrz `docs/ROADMAP.md` (etap 1: import DWG/DXF w przeglądarce i wiele projektów · etap 2: eksport DXF + PDF
rzutów · etap 3: raport kontrolny · równolegle: przepisanie `legacy/page.js` na moduły TypeScript).
