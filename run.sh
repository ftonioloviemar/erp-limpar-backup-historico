#!/bin/bash

# Garante que o script seja executado a partir do seu próprio diretório
cd "$(dirname "$0")"

echo "Executando o script de limpeza de backups..."

# Executa o script Python usando o ambiente virtual gerenciado pelo uv.
uv run python limpar_backups.py
