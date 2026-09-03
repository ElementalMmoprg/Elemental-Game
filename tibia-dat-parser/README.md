# Parser do tibia.dat → tibia_data.json

Extrai do `tibia.dat` do client Tibia (pasta `Dezembro 16, 2025 update_7`) as
propriedades de colisão/posicionamento de cada item e a lista de sprite IDs de
cada item e outfit (monstro), gerando `tibia_data.json` na raiz do
`Elemental-Game`.

## Como rodar de novo (se o tibia.dat for atualizado)

```
python3 build_json.py "<caminho para a pasta com tibia.dat>/tibia.dat" tibia_data.json
```

Requer só Python 3 padrão (sem dependências externas). Roda em poucos segundos.

## O que foi validado

O parser lê sequencialmente: header → 29.410 items → 8.746 outfits → 2.368
effects → missiles, e a posição final bate **exatamente** com o tamanho do
arquivo (31.782.626 bytes) — ou seja, todo o arquivo foi decodificado byte a
byte sem sobras nem faltas, o que é a validação mais forte possível para um
formato binário sem documentação oficial.

Duas descobertas específicas deste arquivo (não são universais do formato
Tibia, são particularidades deste client customizado):

1. **Missile count no header está errado**: o header diz 238 missiles, mas só
   existem 139 até o fim do arquivo. `build_json.py` já trata isso (para
   assim que os bytes acabam) e registra `missileCountActual` no `meta`.
2. **~99 items (a partir do id 29411) usam um layout de "frame group" com
   múltiplos grupos** (o mesmo esquema que outfits usam para idle/andando),
   diferente do resto dos ~29.311 items que usam um único grupo direto. Isso
   provavelmente reflete itens customizados adicionados por uma ferramenta
   diferente da que gerou o client base. O parser detecta isso
   automaticamente por item (tenta o layout simples, se dimensões vierem
   zeradas tenta o layout múltiplo), então não precisa saber de antemão quais
   ids são quais.

## Formato do tibia_data.json

```jsonc
{
  "meta": { "itemCount": 29410, "outfitCount": 8746, ... },
  "items": {
    "<id>": {
      "flags": ["notWalkable", "blockProjectile", ...],   // só flags relevantes p/ colisão/posicionamento
      "groundSpeed": 100,          // só presente se o item for "ground" (chão andável)
      "fg": { "w":1,"h":1,"layers":1,"px":4,"py":1,"pz":1,"phases":1, "sprites":[1234] }
      // OU, para os ~99 itens "multi": "groups": { "0": {...fg...}, "1": {...fg...} }
    }
  },
  "outfits": {
    "<id>": {
      "flags": [...],
      "groups": { "0": {...fg (idle)...}, "1": {...fg (andando)...} }
      // outfits sem animação de caminhada usam "fg" direto, igual aos items
    }
  }
}
```

`fg.sprites` é a lista crua de sprite IDs do `tibia.spr` (32×32 px cada,
ainda comprimidos em RLE lá dentro) na ordem
`width × height × layers × patternX × patternY × patternZ × phases`. Ainda
não decodificamos os PIXELS desses sprites (isso é outro passo — o
`tibia.spr` tem 1.2GB e ~1 milhão de sprites, então vale decidir com calma
quais IDs realmente precisamos renderizar antes de decodificar em massa).

## flags de colisão disponíveis por item

`notWalkable`, `notMoveable`, `blockProjectile`, `notPathable`, `pickupable`,
`stackable`, `container`, `fluidContainer`, `hangable`, `rotateable`,
`onTop`, `onBottom`, `groundBorder`, `fullGround`.

No motor JS, um item é "sólido" (bloqueia o jogador) tipicamente quando tem
`notWalkable` nas flags.
