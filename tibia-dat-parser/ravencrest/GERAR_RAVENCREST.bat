@echo off
cd /d "%~dp0"
echo Extraindo os sprites da cidade de Ravencrest (atlas)...
node extrair_sprites.js "..\..\otcv_8\data\things\1098\Tibia.spr" jobs_ravencrest_atlas.json ravencrest > log_ravencrest.txt 2>&1
type log_ravencrest.txt
echo.
echo Pronto. Pode fechar esta janela.
pause
