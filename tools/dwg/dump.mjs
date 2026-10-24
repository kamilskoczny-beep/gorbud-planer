import { Dwg_File_Type, LibreDwg } from '@mlightcad/libredwg-web';
import fs from 'node:fs';

const [,, inPath, outPath] = process.argv;
const libredwg = await LibreDwg.create('./node_modules/@mlightcad/libredwg-web/wasm/');
const buf = fs.readFileSync(inPath);
const dwg = libredwg.dwg_read_data(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), Dwg_File_Type.DWG);
const db = libredwg.convert(dwg);
libredwg.dwg_free(dwg);

// summary
const ents = db.entities || [];
const byType = {};
for (const e of ents) byType[e.type] = (byType[e.type] || 0) + 1;
console.log('entities:', ents.length, byType);
console.log('layers:', Object.keys(db.tables?.LAYER?.entries || {}).length);
console.log('blocks:', Object.keys(db.blocks || {}).length);
fs.writeFileSync(outPath, JSON.stringify(db, (k, v) => typeof v === 'bigint' ? v.toString() : v));
console.log('written', outPath);
