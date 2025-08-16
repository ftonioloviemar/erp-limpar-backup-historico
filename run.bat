@echo off
REM Executa o script Python usando o ambiente virtual gerenciado pelo uv.
echo Executando o script de limpeza de backups...

uv run python limpar_backups.py

echo.
echo Pressione qualquer tecla para sair...
pause > nul
