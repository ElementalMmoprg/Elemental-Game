// extrair_sprites.js — roda NO PC, ao lado do Tibia.spr. Sem dependências (só Node).
// Lê o .spr com leituras pontuais (offset table + bytes de cada sprite), nunca o arquivo inteiro.
// Uso: node extrair_sprites.js <Tibia.spr> <jobs.json> <pasta_saida>
'use strict';
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const [sprPath, jobsPath, outDir] = process.argv.slice(2);
const fd = fs.openSync(sprPath, 'r');
const hdr = Buffer.alloc(8); fs.readSync(fd, hdr, 0, 8, 0);
const count = hdr.readUInt32LE(4);
const cache = new Map();
function tile(sid) {
  if (cache.has(sid)) return cache.get(sid);
  const px = Buffer.alloc(32 * 32 * 4);
  if (sid > 0 && sid <= count) {
    const ob = Buffer.alloc(4); fs.readSync(fd, ob, 0, 4, 8 + (sid - 1) * 4);
    const off = ob.readUInt32LE(0);
    if (off) {
      const h = Buffer.alloc(5); fs.readSync(fd, h, 0, 5, off);
      const size = h.readUInt16LE(3);
      const data = Buffer.alloc(size); fs.readSync(fd, data, 0, size, off + 5);
      let p = 0, i = 0;
      while (i + 4 <= data.length && p < 1024) {
        const t = data.readUInt16LE(i), c = data.readUInt16LE(i + 2); i += 4; p += t;
        const n = Math.min(c, 1024 - p);
        if (n > 0) data.copy(px, p * 4, i, i + n * 4);
        i += c * 4; p += c;
      }
    }
  }
  if (cache.size < 30000) cache.set(sid, px);
  return px;
}
function crc32(buf) { return zlib.crc32(buf) >>> 0; }
function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type), data]);
  const c = Buffer.alloc(4); c.writeUInt32BE(crc32(td));
  return Buffer.concat([len, td, c]);
}
function png(w, h, rgba) {
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 4 + 1)] = 0; rgba.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4); }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}
const jobs = JSON.parse(fs.readFileSync(jobsPath, 'utf8'));
let done = 0, empty = 0;
for (const j of jobs) {
  let W = j.w, H = j.h; const img = Buffer.alloc(W * H * 4);
  for (const [sid, ox, oy] of j.tiles) {
    const t = tile(sid);
    for (let y = 0; y < 32; y++) {
      const dy = oy + y; if (dy < 0 || dy >= H) continue;
      for (let x = 0; x < 32; x++) {
        const dx = ox + x; if (dx < 0 || dx >= W) continue;
        const s = (y * 32 + x) * 4, a = t[s + 3]; if (!a) continue;
        const d = (dy * W + dx) * 4;
        if (a === 255 || img[d + 3] === 0) { t.copy(img, d, s, s + 4); continue; }
        const da = img[d + 3] / 255, sa = a / 255, oa = sa + da * (1 - sa);
        for (let k = 0; k < 3; k++) img[d + k] = Math.round((t[s + k] * sa + img[d + k] * da * (1 - sa)) / oa);
        img[d + 3] = Math.round(oa * 255);
      }
    }
  }
  let out = img;
  if (j.crop) {
    let x0 = W, y0 = H, x1 = -1, y1 = -1;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (img[(y * W + x) * 4 + 3]) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    if (x1 >= 0) {
      const nw = x1 - x0 + 1, nh = y1 - y0 + 1; out = Buffer.alloc(nw * nh * 4);
      for (let y = 0; y < nh; y++) img.copy(out, y * nw * 4, ((y + y0) * W + x0) * 4, ((y + y0) * W + x1 + 1) * 4);
      W = nw; H = nh;
    } else empty++;
  }
  const p = path.join(outDir, j.out);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, png(W, H, out));
  if (++done % 100 === 0) console.log(`${done}/${jobs.length}`);
}
fs.closeSync(fd);
console.log(`PRONTO: ${done} PNGs em ${outDir} (${empty} vazios)`);
