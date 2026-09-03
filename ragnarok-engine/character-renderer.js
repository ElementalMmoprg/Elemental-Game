/*
 * ============================================================================
 * character-renderer.js
 * ----------------------------------------------------------------------------
 * Motor de renderização de personagem estilo Ragnarok Online (2 spritesheets
 * independentes: CORPO e CABEÇA, sobrepostas em runtime via Canvas 2D).
 *
 * ARQUITETURA (resumo):
 *   - O spritesheet de CORPO guarda só 5 direções reais (Sul, Sudeste, Leste,
 *     Nordeste, Norte). As outras 3 (Sudoeste, Oeste, Noroeste) são a MESMA
 *     arte espelhada horizontalmente em runtime com ctx.scale(-1,1) — é assim
 *     que o RO original economiza espaço de sprite.
 *   - O spritesheet de CABEÇA tem 1 frame estático por direção (não anima
 *     passada), também reaproveitando o espelhamento pras mesmas 3 direções.
 *   - Corpo e cabeça são desenhados em camadas (corpo primeiro, cabeça em
 *     cima), e a cabeça usa uma matriz de offsets X/Y por frame de caminhada
 *     pra acompanhar o "bobbing" (sobe/desce) do tronco durante a passada.
 *   - O espelhamento é aplicado UMA VEZ por personagem (ctx.save/translate/
 *     scale/restore) envolvendo o desenho das DUAS camadas. Isso garante que
 *     o offset da cabeça espelha automaticamente junto com o corpo, sem
 *     precisar inverter manualmente o sinal de X em cada direção espelhada —
 *     é a forma correta e a que menos gera bug de "cabeça foi pro lado errado".
 *
 * CALIBRAGEM — TUDO fica em UM objeto: RagnarokRenderer.config
 *   Todo o motor LÊ os valores de dentro de `config` em tempo de desenho
 *   (nada é copiado pra uma constante fixa "congelada"). Isso significa que
 *   dá pra abrir o DevTools do navegador, digitar por exemplo:
 *
 *       RagnarokRenderer.config.HEAD_BASE_OFFSET.y = -8
 *       RagnarokRenderer.config.BODY_FRAME_W = 70
 *       RagnarokRenderer.config.HEAD_WALK_OFFSETS.E[3] = { x: 2, y: -3 }
 *
 *   ...e ver o efeito no PRÓXIMO frame desenhado, sem precisar recarregar a
 *   página. É assim que se calibra pixel a pixel:
 *   1. BODY_FRAME_W / BODY_FRAME_H — tamanho exato de UM quadro do corpo.
 *   2. HEAD_FRAME_W / HEAD_FRAME_H — tamanho exato de UM quadro da cabeça.
 *   3. BODY_ROW_INDEX — linha (0-based) de cada direção real no sheet do
 *      corpo, caso não bata com "linha 2=Sul...linha 6=Norte" do enunciado.
 *   4. HEAD_FRAME_COORDS — coluna/linha (0-based) de cada direção real no
 *      sheet da cabeça.
 *   5. BODY_ANCHOR_Y_FROM_BOTTOM — se o "pé" não estiver na base do frame.
 *   6. HEAD_BASE_OFFSET — posição da cabeça parado (frame 0).
 *   7. HEAD_WALK_OFFSETS — o quanto a cabeça soma ao offset base em CADA um
 *      dos 8 frames da passada, por direção real (o "bobbing").
 * ============================================================================
 */

(function (global) {
  'use strict';

  // ==========================================================================
  // 1. CONFIG — objeto único e mutável. TUDO abaixo é lido daqui em runtime,
  //    nunca copiado pra uma const separada, pra calibragem ao vivo funcionar
  //    de verdade (ver comentário acima).
  // ==========================================================================

  function buildDefaultBobbing(walkFrameCount) {
    // Padrão de exemplo: sobe/desce suave ao longo dos 8 frames (estilo
    // "passo duplo" clássico de RO: dois ciclos de bob por volta completa).
    // Ajuste os números à vontade — são só um ponto de partida plausível.
    const bobY = [0, -1, -2, -1, 0, -1, -2, -1];
    const swayX = [0, 1, 1, 0, 0, -1, -1, 0];
    const dirs = ['S', 'SE', 'E', 'NE', 'N'];
    const hasLateralSway = { S: false, SE: true, E: true, NE: true, N: false };
    const table = {};
    for (const d of dirs) {
      table[d] = [];
      for (let f = 0; f < walkFrameCount; f++) {
        table[d].push({
          x: hasLateralSway[d] ? (swayX[f % swayX.length]) : 0,
          y: bobY[f % bobY.length],
        });
      }
    }
    return table;
  }

  const WALK_FRAME_COUNT_DEFAULT = 8;

  const CONFIG = {
    // --- Tamanho de UM frame de cada spritesheet (pixels, na imagem-fonte) ---
    BODY_FRAME_W: 64,
    BODY_FRAME_H: 64,
    HEAD_FRAME_W: 32,
    HEAD_FRAME_H: 32,

    // --- Quantos frames horizontais tem o walk cycle do corpo ---
    WALK_FRAME_COUNT: WALK_FRAME_COUNT_DEFAULT,

    // --- Linha (0-based) de cada direção real no sheet de CORPO.
    //     Enunciado: linha 2=Sul, 3=Sudeste, 4=Leste, 5=Nordeste, 6=Norte
    //     (1-based) => índices 1..5 abaixo (0-based). ---
    BODY_ROW_INDEX: { S: 1, SE: 2, E: 3, NE: 4, N: 5 },

    // --- Coluna/linha (0-based) do frame estático de cada direção real no
    //     sheet de CABEÇA (não anima passada, é 1 frame fixo por direção). ---
    HEAD_FRAME_COORDS: {
      S: { col: 0, row: 0 },
      SE: { col: 1, row: 0 },
      E: { col: 2, row: 0 },
      NE: { col: 3, row: 0 },
      N: { col: 4, row: 0 },
    },

    // --- Distância (px) da base do frame até o "chão"/pé do personagem.
    //     Aumente se o frame tiver espaço vazio embaixo. ---
    BODY_ANCHOR_Y_FROM_BOTTOM: 0,

    // --- Posição BASE da cabeça (parado, frame 0), relativa ao topo do
    //     frame do corpo. x=0 centraliza; y negativo sobe a cabeça. ---
    HEAD_BASE_OFFSET: { x: 0, y: -4 },

    // --- Matriz de offsets do "bobbing": HEAD_WALK_OFFSETS[dirReal][frame]
    //     = {x,y} somado ao HEAD_BASE_OFFSET em cada um dos 8 frames. ---
    HEAD_WALK_OFFSETS: buildDefaultBobbing(WALK_FRAME_COUNT_DEFAULT),

    // --- Duração (ms) de cada frame da caminhada. Estilo retrô = passo
    //     truncado (sem interpolação). ---
    WALK_FRAME_DURATION_MS: 120,

    // --- Velocidade de movimento (pixels/segundo). ---
    MOVE_SPEED_PX_S: 90,

    // --- Mapa das 8 direções -> direção real (linha) + espelhar ou não. ---
    DIRECTION_INFO: {
      S: { row: 'S', mirror: false },
      SE: { row: 'SE', mirror: false },
      E: { row: 'E', mirror: false },
      NE: { row: 'NE', mirror: false },
      N: { row: 'N', mirror: false },
      NW: { row: 'NE', mirror: true }, // reaproveita Nordeste espelhado
      W: { row: 'E', mirror: true },   // reaproveita Leste espelhado
      SW: { row: 'SE', mirror: true }, // reaproveita Sudeste espelhado
    },
  };

  // ==========================================================================
  // 2. INPUT — WASD/setas -> uma das 8 direções
  // ==========================================================================

  function directionFromInput(input) {
    const up = input.up, down = input.down, left = input.left, right = input.right;
    if (up && right) return 'NE';
    if (up && left) return 'NW';
    if (down && right) return 'SE';
    if (down && left) return 'SW';
    if (up) return 'N';
    if (down) return 'S';
    if (left) return 'W';
    if (right) return 'E';
    return null; // nenhuma tecla pressionada
  }

  const MOVE_VECTORS = {
    N: { x: 0, y: -1 }, S: { x: 0, y: 1 },
    E: { x: 1, y: 0 }, W: { x: -1, y: 0 },
    NE: { x: Math.SQRT1_2, y: -Math.SQRT1_2 },
    NW: { x: -Math.SQRT1_2, y: -Math.SQRT1_2 },
    SE: { x: Math.SQRT1_2, y: Math.SQRT1_2 },
    SW: { x: -Math.SQRT1_2, y: Math.SQRT1_2 },
  };

  // ==========================================================================
  // 3. AnimatedCharacter — estado, física e animação
  // ==========================================================================

  class AnimatedCharacter {
    constructor(opts) {
      opts = opts || {};
      this.x = opts.x || 0;
      this.y = opts.y || 0;
      this.dir = opts.dir || 'S';   // direção atual (uma das 8)
      this.frameIndex = 0;          // frame atual do walk cycle (0..N-1)
      this._animAccumMs = 0;        // acumulador do passo "truncado"
      this.moving = false;
    }

    /**
     * @param {number} dt - delta time em segundos
     * @param {{up:boolean,down:boolean,left:boolean,right:boolean}} input
     */
    update(dt, input) {
      const dir = directionFromInput(input);
      this.moving = dir !== null;

      if (this.moving) {
        this.dir = dir;

        // --- física: movimento contínuo, suave, em pixels/segundo ---
        const v = MOVE_VECTORS[dir];
        const speed = CONFIG.MOVE_SPEED_PX_S;
        this.x += v.x * speed * dt;
        this.y += v.y * speed * dt;

        // --- animação: acumulador em ms; só avança quando estoura a
        //     duração do frame configurada — NUNCA interpola (retrô). ---
        const frameMs = CONFIG.WALK_FRAME_DURATION_MS;
        const frameCount = CONFIG.WALK_FRAME_COUNT;
        this._animAccumMs += dt * 1000;
        while (this._animAccumMs >= frameMs) {
          this._animAccumMs -= frameMs;
          this.frameIndex = (this.frameIndex + 1) % frameCount;
        }
      } else {
        // parado: volta pro frame de descanso e zera o acumulador, pra
        // sempre reiniciar o ciclo do mesmo jeito ao voltar a andar.
        this.frameIndex = 0;
        this._animAccumMs = 0;
      }
    }
  }

  // ==========================================================================
  // 4. RENDERIZAÇÃO — corpo + cabeça em camadas, espelhamento único
  // ==========================================================================

  /**
   * @param {CanvasRenderingContext2D} ctx
   * @param {AnimatedCharacter} character
   * @param {HTMLImageElement} bodyImg - spritesheet do corpo
   * @param {HTMLImageElement} headImg - spritesheet da cabeça
   * @param {{debug?: boolean}} [opts]
   */
  function drawCharacter(ctx, character, bodyImg, headImg, opts) {
    opts = opts || {};
    const info = CONFIG.DIRECTION_INFO[character.dir];
    const rowKey = info.row;
    const mirror = info.mirror;

    const bW = CONFIG.BODY_FRAME_W, bH = CONFIG.BODY_FRAME_H;
    const hW = CONFIG.HEAD_FRAME_W, hH = CONFIG.HEAD_FRAME_H;

    const bodyRow = CONFIG.BODY_ROW_INDEX[rowKey];
    const bodySx = character.frameIndex * bW;
    const bodySy = bodyRow * bH;

    const headCoord = CONFIG.HEAD_FRAME_COORDS[rowKey];
    const headSx = headCoord.col * hW;
    const headSy = headCoord.row * hH;

    const bobTable = CONFIG.HEAD_WALK_OFFSETS[rowKey] || [];
    const bob = bobTable[character.frameIndex] || { x: 0, y: 0 };
    const base = CONFIG.HEAD_BASE_OFFSET;
    const headOffsetX = base.x + bob.x;
    const headOffsetY = base.y + bob.y;

    ctx.save();
    // Âncora = pé do personagem (x,y do character = posição no mundo).
    ctx.translate(Math.round(character.x), Math.round(character.y));

    // Espelhamento aplicado UMA VEZ, envolvendo corpo E cabeça — o offset
    // da cabeça espelha automaticamente junto, sem inverter sinal na mão.
    if (mirror) ctx.scale(-1, 1);

    // --- Camada 1: CORPO (pé em y=0, centralizado em x=0) ---
    const bodyDrawY = -bH + CONFIG.BODY_ANCHOR_Y_FROM_BOTTOM;
    ctx.drawImage(
      bodyImg,
      bodySx, bodySy, bW, bH,
      Math.round(-bW / 2), Math.round(bodyDrawY),
      bW, bH
    );

    // --- Camada 2: CABEÇA (em cima do corpo, na âncora + offset do frame) ---
    const headDrawX = -hW / 2 + headOffsetX;
    const headDrawY = bodyDrawY + headOffsetY;
    ctx.drawImage(
      headImg,
      headSx, headSy, hW, hH,
      Math.round(headDrawX), Math.round(headDrawY),
      hW, hH
    );

    if (opts.debug) {
      // Overlay de depuração: cruz na âncora (pé) + retângulo da cabeça —
      // ajuda a calibrar offsets vendo exatamente onde cada camada cai.
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(-6, 0); ctx.lineTo(6, 0);
      ctx.moveTo(0, -6); ctx.lineTo(0, 6);
      ctx.stroke();
      ctx.strokeStyle = 'rgba(255,0,0,0.8)';
      ctx.strokeRect(Math.round(headDrawX), Math.round(headDrawY), hW, hH);
    }

    ctx.restore();
  }

  // ==========================================================================
  // 5. API pública
  // ==========================================================================

  global.RagnarokRenderer = {
    AnimatedCharacter,
    drawCharacter,
    directionFromInput,
    config: CONFIG, // objeto mutável — calibre direto pelo devtools/console
  };
})(typeof window !== 'undefined' ? window : globalThis);
