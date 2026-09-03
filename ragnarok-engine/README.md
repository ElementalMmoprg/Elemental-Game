# Ragnarok-style Character Renderer

Motor de renderização de personagem em Canvas 2D vanilla (sem dependências),
separado em duas camadas independentes — **corpo** e **cabeça** — igual a
arquitetura clássica do Ragnarok Online, conforme especificado.

## Arquivos

- `character-renderer.js` — o motor em si (classe `AnimatedCharacter`, função
  `drawCharacter`, mapeamento de direções/teclado). É o arquivo que importa
  pro seu jogo.
- `demo.html` — página de teste/calibração: WASD pra mover em 8 direções,
  tecla `G` liga/desliga overlay de debug (mostra a âncora e o retângulo da
  cabeça), tecla `P` pausa num frame pra você examinar com calma.
- `placeholder_body.png` / `placeholder_head.png` — spritesheets **sintéticos
  de teste** (não são arte de jogo!). Servem só pra validar a mecânica do
  motor: cada quadro tem uma cor por direção e um marquinho preto assimétrico
  do lado direito, pra dar pra enxergar visualmente se o espelhamento
  (`ctx.scale(-1,1)`) está virando pro lado certo. **Troque esses dois
  arquivos pelos seus spritesheets reais** (só mudar `bodyImg.src` /
  `headImg.src` no topo do `demo.html`).
- `make_placeholder_sprites.py` — script Python que gerou os dois PNGs
  acima, incluído só de referência (não precisa rodar).

## Como usar com os SEUS spritesheets

1. Abra `demo.html` num servidor local (não funciona com `file://` direto
   por causa de CORS no `<img>`; um jeito fácil no Windows é rodar
   `python -m http.server 8000` dentro da pasta e abrir
   `http://localhost:8000/demo.html`, ou usar a extensão "Live Server" do
   VS Code).
2. Troque `bodyImg.src` e `headImg.src` (topo do `<script>` do `demo.html`)
   pelos caminhos dos seus dois spritesheets reais.
3. Abra o DevTools (F12) e ajuste ao vivo, sem precisar recarregar a página:
   ```js
   RagnarokRenderer.config.BODY_FRAME_W = 70   // largura real de 1 frame do corpo
   RagnarokRenderer.config.BODY_FRAME_H = 90   // altura real de 1 frame do corpo
   RagnarokRenderer.config.HEAD_FRAME_W = 40
   RagnarokRenderer.config.HEAD_FRAME_H = 40
   RagnarokRenderer.config.HEAD_BASE_OFFSET.y = -12   // sobe/desce a cabeça
   RagnarokRenderer.config.HEAD_WALK_OFFSETS.E[3] = { x: 2, y: -3 } // bobbing por frame
   ```
   Tudo isso é lido em tempo real pelo motor — dá pra ir ajustando pixel a
   pixel olhando o resultado, e só depois copiar os valores finais de volta
   pro `character-renderer.js` (na seção `CONFIG`, bem no topo do arquivo).
4. Se as linhas do seu sheet de corpo não forem exatamente "linha 2=Sul,
   3=Sudeste, 4=Leste, 5=Nordeste, 6=Norte", ajuste
   `RagnarokRenderer.config.BODY_ROW_INDEX`. Se o sheet de cabeça não seguir
   a mesma ordem em colunas, ajuste `HEAD_FRAME_COORDS`.

## Direções e espelhamento

Só existem 5 direções "reais" no sheet: Sul, Sudeste, Leste, Nordeste, Norte.
As outras 3 (Sudoeste, Oeste, Noroeste) reaproveitam a arte de
Sudeste/Leste/Nordeste espelhada horizontalmente — exatamente como pedido.
O espelhamento é aplicado **uma vez só**, envolvendo corpo e cabeça juntos,
então os offsets da cabeça (`HEAD_WALK_OFFSETS`) espelham automaticamente
junto com o corpo — não precisa inverter sinal de X na mão pra cada direção
espelhada (isso evita exatamente o tipo de bug de "cabeça foi pro lado
errado" que já tivemos antes no `world-prototype.html`).

## O que foi testado

- **35 testes automatizados** (`test_logic.js`, roda no Chromium real via
  Playwright, contra o `character-renderer.js` de verdade — não uma cópia):
  mapeamento de teclado pras 8 direções, seleção correta de linha/coluna do
  sprite pra cada direção, espelhamento aplicado exatamente nas 3 direções
  certas (e só nelas), truncamento correto da animação (sem interpolação),
  reset do frame ao parar. **Todos passaram.**
- **Verificação visual** com os spritesheets sintéticos: capturas de tela
  das 8 direções mostrando que o marco assimétrico troca de lado
  corretamente quando espelha, e que a cabeça realmente se desloca
  (bobbing) entre os frames da caminhada.
- **Isso NÃO substitui testar com seus spritesheets reais.** Os placeholders
  só provam que a lógica do motor está certa — o resultado visual final com
  arte de verdade depende de calibrar `BODY_FRAME_W/H`, `HEAD_FRAME_W/H`,
  `BODY_ROW_INDEX`, `HEAD_FRAME_COORDS` e os offsets pros valores exatos dos
  seus arquivos.

## Ainda não integrado ao jogo

Este motor está isolado, standalone — não mexi no `world-prototype.html`.
Quando você tiver os spritesheets no formato Ragnarok (corpo separado de
cabeça, layout de linhas/colunas como descrito), me avisa que eu integro
esse motor no jogo de verdade, substituindo o sistema de sprite atual
(que usa um atlas de corpo com 4 direções + atlas de cabeça por
hairstyle — bem diferente desse layout).
