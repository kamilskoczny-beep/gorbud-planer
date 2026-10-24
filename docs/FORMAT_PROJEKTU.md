# Format pliku projektu `.planer.json` (schema 1)

```jsonc
{
  "id": "drawsko-pocztowa11",      // slug, klucz w magazynie
  "schema": 1,
  "name": "Pocztowa 11",
  "subtitle": "Drawsko Pomorskie · model roboczy zmiany sposobu użytkowania",
  "createdAt": "2026-10-24T13:00:00Z", "updatedAt": "…",
  "model": {                        // wynik tools/dwg – geometria istniejąca (mm, układ lokalny kondygnacji, y w górę)
    "px": 20,
    "floors": {
      "pietro1": {
        "name": "I piętro",
        "bbox": [0,0,25647,24188],
        "geo": { "walls": [ {"k":"l","p":[[x,y],[x,y]]}, {"k":"a","c":[x,y],"r":600,"a0":0,"a1":1.57} ],
                 "windows": [], "doors": [], "stairs": [], "sills": [], "fixtures": [], "dims": [], "ceiling": [], "hatch": [] },
        "texts": [ {"x":0,"y":0,"t":"108","h":180,"r":0} ],
        "rooms": [ {"nr":"108","name":"pokój","area":88.68,"h":"h_sufitu = 344 cm","lx":0,"ly":0,"poly":[[x,y],…],"parea":88.5} ]
      }
    }
  },
  "variants": {
    "units": { "M1": {"name":"M1 — 108 jako 1 mieszkanie","color":"#e0a04a"} },
    "floors": { "pietro1": [ {"id":"P9","name":"…","desc":"…","assign":{"108":"M1"},"hide":["108"]} ] },
    "attic":  { "floor":"poddasze","hmin":900,"planes":[ {"line":[[x,y],[x,y]],"dir":[-1,0],"h0":2775,"tan":1.04,"room":"213/216"} ] }
  },
  "items": {                        // elementy projektowane per kondygnacja
    "pietro1": [
      {"id":"abc1234","type":"wall","pts":[[x,y],[x,y]],"w":120,"v":"P9"},
      {"id":"…","type":"demo","pts":[[x,y],[x,y]],"w":430,"label":"wyburzenie 2,63 m"},
      {"id":"…","type":"door","pts":[[x,y],[x,y]],"w":160,"flip":false,"open":false},   // pts = światło otworu; w = grubość ściany+40
      {"id":"…","type":"room","pts":[…],"holes":[[…]],"anchor":[x,y],"label":"salon","unit":"M1","color":"#f4a261","auto":true},
      {"id":"…","type":"furn","kind":"pax200","pts":[[x0,y0],[x1,y1]],"rot":0,"label":"PAX 200×58"},
      {"id":"…","type":"dim","pts":[[x,y],[x,y]]},
      {"id":"…","type":"note","pts":[[x,y]],"label":"…"},
      {"id":"…","type":"ink","pts":[…]}, {"id":"…","type":"arrow","pts":[[x,y],[x,y]],"label":"…"}, {"id":"…","type":"mark","n":1,"pts":[[x,y]],"label":"…"}
    ]
  },
  "ui": { "layers": {"dims":false}, "variants": {"pietro1":"P9"} }
}
```

Zasady:
- Jednostki: milimetry; współrzędne lokalne kondygnacji (origin = min bbox ścian; parter przesunięty, by klatka schodowa pokrywała się z resztą).
- `v` w elemencie = widoczny tylko w tym wariancie; brak `v` = we wszystkich.
- Pole `pts` ściany to **oś**; grubość `w`. Drzwi: `pts` = światło przejścia (80 cm standard); otwór w murze = światło + 2×45 mm ościeżnicy.
- Pomieszczenie z `auto !== false` ma obrys przeliczany ze ścian od punktu `anchor`; `pts`/`holes` to ostatni wynik (zapisany dla kopii offline).
