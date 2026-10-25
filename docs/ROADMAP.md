# Mapa drogowa

## Etap 0 – przeniesienie (zrobione 24.10.2026)
- [x] Repozytorium, aplikacja Vite/TS, magazyn projektów, import/eksport `.planer.json`
- [x] Edytor z modelu roboczego Pocztowa 11 uruchamiany w aplikacji (ten sam kod co artefakt)
- [x] Dane Drawska: model, warianty, układ 108, archiwum 13 wariantów
- [ ] Repozytorium na GitHub (konto użytkownika) + pierwsza publikacja (GitHub Pages lub plik dist)

## Etap 1 – import i wiele projektów
- [ ] Import DWG w przeglądarce (@mlightcad/libredwg-web jako WASM) i DXF (parser tekstowy)
- [ ] Kreator nowego projektu: wybór warstw (ściany/okna/drzwi/opisy), wykrywanie arkuszy kondygnacji, wyrównanie kondygnacji (korelacja rastrów ścian jak w `variants.align` – 25.10.2026 zrobione offline w Pythonie, do przeniesienia do przeglądarki)
- [x] Podrys innej kondygnacji i piony instalacyjne widoczne na wszystkich kondygnacjach (25.10.2026)
- [ ] Pomieszczenia z inwentaryzacji przez flood fill w przeglądarce (ten sam algorytm co dla projektowanych)
- [ ] Wysokości: odczyt `h_sufitu`, linie załamania, kreator skosów (kierunek, h0, spadek) zamiast ręcznej tabeli
- [ ] Lista projektów z miniaturami, kopie zapasowe do folderu (File System Access API / OneDrive)

## Etap 2 – eksporty
- [ ] DXF: warstwy (SCIANY_PROJ, WYBURZENIA, DRZWI, MEBLE, POMIESZCZENIA, OPISY), bloki drzwi, teksty powierzchni
- [ ] PDF rzutów: skala, ramka, tabelka, wymiary, zestawienie pomieszczeń i powierzchni użytkowej (PN-ISO 9836), zestawienie drzwi
- [ ] Zestawienie do Excela (powierzchnie lokali, lista PAX, drzwi)

## Etap 3 – raport kontrolny
- [ ] Kolizje mebli ze ścianami i skrzydłami drzwi; dojścia do mebli (min. szerokości)
- [ ] Szerokości przejść i korytarzy, światło drzwi (80 / 90 wejściowe), kierunek otwierania na drogach ewakuacji
- [ ] Wysokości na poddaszu: udział powierzchni h ≥ 2,2 / 1,9, pas 2,2 m na drodze komunikacji
- [x] Długość dojścia ewakuacyjnego – warstwa w edytorze (25.10.2026), drzwi EI 30 / 90 cm
- [ ] Doświetlenie (1:8), bilans PAX (tylko 150/175/200/250/275/300)
- [ ] Raport jako strona w aplikacji + zapis do Projektu Claude

## Równolegle – jakość kodu
- [ ] Przepisanie `legacy/page.js` na moduły TS (geometria → render → UI), testy jednostkowe geometrii
- [ ] three.js z npm zamiast CDN, czcionki lokalnie (praca offline)
- [ ] Historia zmian projektu (migawki) i porównanie wariantów obok siebie
