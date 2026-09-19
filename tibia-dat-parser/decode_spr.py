"""
Decodificador de pixels do export_10.98.spr (RavenDawn) — reconstruído em
19/09/2026 porque o script usado nas sessões passadas (outfits de Arquétipo
442-449, effects_sheet.png, missiles_sheet.png) não sobrou salvo, só os PNGs
finais. Documentando aqui pra nunca mais precisar redescobrir isso.

FORMATO DESCOBERTO (por tentativa e erro, comparando contagens de pixel
decodificado até bater 1024 = 32x32):
- Header do .spr: 4 bytes assinatura (LE) + 4 bytes contagem de sprites (LE,
  formato "extended"/32-bit — client é versão 10.98, que já usa isso).
- Tabela de offsets logo em seguida: 1 entrada de 4 bytes (LE) por sprite,
  1-indexado (sprite id 1 = primeira entrada). offset 0 = sprite vazio/
  transparente.
- Em cada offset: 3 bytes de "chave de transparência" (RGB, sem uso real
  aqui — ver abaixo), 2 bytes (LE) = tamanho dos dados comprimidos que vêm a
  seguir, depois os dados em si.
- Dados comprimidos = sequência de blocos até completar 1024 pixels (32x32):
  [2 bytes LE = qtd de pixels TRANSPARENTES, 2 bytes LE = qtd de pixels
  COLORIDOS, qtd_colorida * 4 bytes (R,G,B,A — ALPHA REAL por pixel, não é
  o formato clássico de colorkey RGB de 3 bytes)]. Esse client usa alpha de
  verdade (bpp=4), diferente do Tibia original de qualquer versão oficial
  conhecida — provavelmente uma extensão do fork RavenDawn.

VALIDADO: decodificando com bpp=4 e header de 3 bytes, o total de bytes
consumidos bate EXATAMENTE com o `size` declarado, pros 3 sprites testados
(2807, 3523, 100) — a validação mais forte possível pra um formato binário
sem documentação.

COMPOSIÇÃO de sprite multi-tile (outfits com w/h > 1, ex. criaturas w=2,h=2):
dentro de um "group" (idle=groups[0], andando=groups[1]), a lista `sprites`
é uma sequência de BLOCOS de w*h tiles cada; block[0] = direção 0, block[1] =
direção 1, etc. (px=4 direções pra maioria das criaturas). DENTRO de cada
bloco, os tiles vêm em ordem raster linha-por-linha (y de cima pra baixo, x
da esquerda pra direita) — validado visualmente com outfit id 2 (vira uma
criatura tipo ave/fênix laranja reconhecível nas 4 direções, ver
sprites-monstro-4-direcoes-notas.md).

Uso:
    python3 decode_spr.py <caminho_do_.spr> <caminho_outfits_dat8_full.json>

Ou importe as funções `decode_tile`/`compose_group_all_directions` direto.
"""
import struct
import sys
import json
from PIL import Image


def offset_for(f, sprite_id):
    f.seek(8 + (sprite_id - 1) * 4)
    return struct.unpack('<I', f.read(4))[0]


def decode_tile(f, sprite_id):
    """Decodifica 1 tile de 32x32 (RGBA) a partir do sprite_id. Nunca lança
    exceção -- em caso de erro/id inválido, devolve um tile vermelho sólido
    (fácil de notar visualmente num contact sheet) em vez de travar o lote
    inteiro; sprite_id apontando pra offset 0 devolve transparente de verdade."""
    try:
        off = offset_for(f, sprite_id)
        if off == 0:
            return Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        f.seek(off)
        f.read(3)  # colorkey -- não usado, este formato tem alpha real
        size = struct.unpack('<H', f.read(2))[0]
        data = f.read(size)
        pixels = []
        i = 0
        while len(pixels) < 1024 and i + 4 <= len(data):
            transp = struct.unpack_from('<H', data, i)[0]; i += 2
            colored = struct.unpack_from('<H', data, i)[0]; i += 2
            pixels += [(0, 0, 0, 0)] * transp
            for _ in range(colored):
                if i + 4 > len(data):
                    break
                r, g, b, a = data[i], data[i + 1], data[i + 2], data[i + 3]
                i += 4
                pixels.append((r, g, b, a))
        while len(pixels) < 1024:
            pixels.append((0, 0, 0, 0))
        im = Image.new('RGBA', (32, 32))
        im.putdata(pixels[:1024])
        return im
    except Exception:
        return Image.new('RGBA', (32, 32), (200, 0, 0, 255))


def compose_group_all_directions(f, group):
    """Devolve uma lista de imagens PIL, uma por 'bloco' (tipicamente 1 por
    direção, px=4 -> 4 imagens) do group indicado (ex. outfit['groups'][0]
    pra idle, [1] pra andando -- andando tem N frames por direção, gerando
    N blocos por direção em sequência, ver len(sprites)//(w*h*frames) se
    quiser separar por frame também)."""
    w, h = group['w'], group['h']
    sprites = group['sprites']
    n_tiles = w * h
    n_blocks = len(sprites) // n_tiles
    out = []
    for b in range(n_blocks):
        block = sprites[b * n_tiles:(b + 1) * n_tiles]
        canvas = Image.new('RGBA', (w * 32, h * 32))
        idx = 0
        for yy in range(h):
            for xx in range(w):
                if idx >= len(block):
                    idx += 1
                    continue
                tile = decode_tile(f, block[idx])
                idx += 1
                canvas.paste(tile, (xx * 32, yy * 32))
        out.append(canvas)
    return out


if __name__ == '__main__':
    spr_path = sys.argv[1]
    outfits_json_path = sys.argv[2]
    outfit_id = sys.argv[3] if len(sys.argv) > 3 else '2'
    with open(outfits_json_path) as jf:
        outfits = json.load(jf)
    entry = outfits[outfit_id]
    with open(spr_path, 'rb') as f:
        for gi, g in enumerate(entry['groups']):
            imgs = compose_group_all_directions(f, g)
            for bi, im in enumerate(imgs):
                out_name = f'outfit{outfit_id}_group{gi}_block{bi}.png'
                im.save(out_name)
                print('saved', out_name, im.size)
