# Ravencrest — gerador da Cidade Principal (21/10/2026)

Recorte real do mapa do Ravendawn (`rd_project/Server/data/world/1098.otbm`),
x 5015–5205, y 5010–5235, andares 2..14, desenhado com o `Tibia.dat/.spr`
de `rd_project/otcv_8/data/things/1098`. O `.spr` (1 GB) nunca sai do PC.

1. `pass3.py`: lê o .otbm e guarda os tiles do recorte (rc_tiles.pkl).
2. `build_rc.py`: liga item de servidor -> cliente (items.otb), lê o .dat
   (camadas, deslocamento, elevação, padrões), calcula andável/bloqueado
   (chão + flag notWalkable) e as trocas de andar (floorchange do items.xml,
   regras do TFS; escada de mão/corda sobe para x, y+1, z-1).
3. `export_rc.py`: grava city.json + floor_<z>.json (Elemental_assets/assets/city/ravencrest).
4. Atlas: `GERAR_RAVENCREST.bat` (com extrair_sprites.js e jobs_ravencrest_atlas.json)
   na pasta rd_project/pacote_elemental/mapa gera atlas_0.png e atlas_1.png.
5. `render_rc.py`: prévia local (PNG) a partir do atlas.
