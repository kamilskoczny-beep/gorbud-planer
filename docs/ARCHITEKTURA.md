# Architektura

## Dziś (etap 0)
- **Powłoka** (`web/src/main.ts`, `store.ts`): lista projektów w IndexedDB, import/eksport `.planer.json`, start edytora.
- **Edytor** (`web/src/legacy/page.js` + `page.body.html` + `page.css`): jeden skrypt (IIFE) przeniesiony 1:1 z modelu
  roboczego. Czyta `#modelData` / `#variantData`, zapisuje przez adapter `window.PLANER` (`loadItems`, `saveItems`).
  Bez adaptera działa jak dawniej (localStorage / baza artefaktu) – dzięki temu artefakt Pocztowa 11 i aplikacja korzystają
  z tego samego kodu do czasu zakończenia przepisywania.
- **Narzędzia** (`tools/`): DWG → JSON (Node WASM libredwg + Python/OpenCV flood fill pomieszczeń), generator wariantów,
  łaty bazy artefaktu.

## Docelowo
```
web/src/
  model/      typy (Project, Floor, Item…), walidacja schematu, migracje
  engine/     geometria: ściany (łączenie, docinanie, przesuwanie, końce, wytnij), drzwi, pomieszczenia (raster+flood fill),
              kolizje mebli, wymiary automatyczne, wysokości (skosy), bilans powierzchni (PN-ISO 9836)
  render/     SVG 2D (warstwy) i three.js 3D – czysto z modelu, bez stanu UI
  ui/         narzędzia, pasek, panele, skróty, edycja inline
  io/         import DWG/DXF (WASM w przeglądarce), eksport DXF (warstwy), PDF (rzuty + zestawienia), .planer.json
  checks/     raport kontrolny (reguły z docs/ZASADY_PROJEKTOWE.md)
```
Przepisywanie idzie funkcja po funkcji: moduł TS zastępuje fragment `page.js`, test w `tests/` pilnuje zgodności wyników
(te same wejścia → te same współrzędne).

## Zasady techniczne
- Stan projektu jest jedynym źródłem prawdy; render zawsze z modelu.
- Każda operacja edycyjna = czysta funkcja `(items, parametry) → items'` (łatwa do testów i do cofania).
- Nic nie liczymy „na oko”: raster pomieszczeń 40 mm, zaokrąglenia do 10 mm, tolerancje jawnie w kodzie.
- Nowa reguła od użytkownika → `docs/ZASADY_PROJEKTOWE.md` + umiejętność + (jeśli automatyzowalna) `checks/`.
