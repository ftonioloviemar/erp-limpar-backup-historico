
import os
import re
import logging
import zipfile
from datetime import datetime, timedelta
from collections import defaultdict

# --- CONFIGURAÇÃO ---
# ATENÇÃO: Altere esta variável para False para apagar os arquivos de verdade.
# Por padrão, o script apenas simula a operação sem deletar nada.
DRY_RUN = True

# --- CONFIGURAÇÃO DE CAMINHO (AJUSTE CONFORME O SISTEMA OPERACIONAL) ---
#
# Diretório onde os backups estão localizados.
#
# Exemplo para Windows:
# DIRETORIO_BACKUPS = r"C:\caminho\para\backups"
#
# Exemplo para Linux:
# DIRETORIO_BACKUPS = "/mnt/servidor/backups"
#
DIRETORIO_BACKUPS = r"C:\temp\tecnicon\diario"


# --- DEMAIS CONFIGURAÇÕES (GERALMENTE NÃO PRECISAM DE ALTERAÇÃO) ---

# Diretório para salvar os arquivos de log. Será criado na mesma pasta do script.
# O uso de os.path.join garante a compatibilidade entre Windows e Linux.
DIRETORIO_LOGS = os.path.join(os.path.dirname(__file__), 'logs')

# Expressão regular para identificar os arquivos de backup.
REGEX_ARQUIVO = re.compile(r"^(emp(\d+)_H_(\d{6})_full_N0_(\d+)_(\d+))\.zip$")


def setup_logging():
    """Configura o sistema de logging para salvar em arquivo e mostrar no console."""
    os.makedirs(DIRETORIO_LOGS, exist_ok=True)
    
    log_filename = datetime.now().strftime("%Y%m%d") + ".log"
    log_filepath = os.path.join(DIRETORIO_LOGS, log_filename)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter('%(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

def compactar_logs_antigos():
    """Compacta arquivos de log com mais de 30 dias."""
    logging.info(f"Verificando logs antigos (mais de 30 dias) em {DIRETORIO_LOGS}")
    try:
        for nome_arquivo in os.listdir(DIRETORIO_LOGS):
            if nome_arquivo.endswith('.log'):
                caminho_log = os.path.join(DIRETORIO_LOGS, nome_arquivo)
                try:
                    data_arquivo = datetime.strptime(nome_arquivo, '%Y%m%d.log')
                    if datetime.now() - data_arquivo > timedelta(days=30):
                        caminho_zip = caminho_log.replace('.log', '.zip')
                        logging.info(f"Compactando log antigo: {nome_arquivo}")
                        with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                            zf.write(caminho_log, arcname=nome_arquivo)
                        os.remove(caminho_log)
                except ValueError:
                    logging.warning(f"Arquivo de log '{nome_arquivo}' não corresponde ao formato de data esperado e será ignorado.")
                    continue
    except Exception as e:
        logging.error(f"Erro ao compactar logs antigos: {e}")


def encontrar_e_agrupar_arquivos():
    """Agrupa arquivos de backup que correspondem ao padrão."""
    if not os.path.isdir(DIRETORIO_BACKUPS):
        logging.error(f"O diretório de backups configurado '{DIRETORIO_BACKUPS}' não foi encontrado ou não é um diretório válido.")
        return None

    logging.info(f"Analisando diretório: {DIRETORIO_BACKUPS}")
    arquivos_agrupados = defaultdict(list)

    for nome_arquivo in os.listdir(DIRETORIO_BACKUPS):
        match = REGEX_ARQUIVO.match(nome_arquivo)
        if match:
            chave_grupo = f"emp{match.group(2)}_H_{match.group(3)}"
            caminho_completo = os.path.join(DIRETORIO_BACKUPS, nome_arquivo)
            arquivos_agrupados[chave_grupo].append(caminho_completo)

    return arquivos_agrupados


def processar_grupos(arquivos_agrupados):
    """Processa os grupos de arquivos, decidindo quais manter e quais excluir."""
    if not arquivos_agrupados:
        logging.info("Nenhum arquivo de backup correspondente ao padrão foi encontrado.")
        return

    total_a_excluir, total_a_manter = 0, 0

    logging.info("--- Relatório de Limpeza de Backups ---")
    if DRY_RUN:
        logging.warning("AVISO: Rodando em modo de simulação (DRY_RUN=True). Nenhum arquivo será excluído.")
    else:
        logging.warning("AVISO: Rodando em modo de exclusão (DRY_RUN=False). Arquivos marcados serão excluídos.")

    for chave_grupo, arquivos in sorted(arquivos_agrupados.items()):
        if len(arquivos) <= 1:
            logging.info(f"\n--- Grupo: {chave_grupo} (1 arquivo, nada a fazer) ---")
            logging.info(f"MANTER: {os.path.basename(arquivos[0])}")
            total_a_manter += 1
            continue

        arquivos.sort()
        arquivo_a_manter = arquivos[-1]
        arquivos_a_excluir = arquivos[:-1]

        logging.info(f"\n--- Grupo: {chave_grupo} ({len(arquivos)} arquivos) ---")
        logging.info(f"MANTER: {os.path.basename(arquivo_a_manter)}")
        total_a_manter += 1

        for arquivo in arquivos_a_excluir:
            logging.info(f"EXCLUIR: {os.path.basename(arquivo)}")
            total_a_excluir += 1
            if not DRY_RUN:
                try:
                    os.remove(arquivo)
                    logging.info(f"  -> Arquivo '{os.path.basename(arquivo)}' excluído com sucesso.")
                except OSError as e:
                    logging.error(f"  -> ERRO ao excluir o arquivo: {e}")

    logging.info("\n--- Resumo da Operação ---")
    logging.info(f"Total de arquivos a manter: {total_a_manter}")
    logging.info(f"Total de arquivos a excluir: {total_a_excluir}")
    if DRY_RUN:
        logging.warning("\nPara excluir os arquivos, edite o script e mude a variável DRY_RUN para False.")
    else:
        logging.info("\nOperação de exclusão finalizada.")


if __name__ == "__main__":
    setup_logging()
    compactar_logs_antigos()
    grupos = encontrar_e_agrupar_arquivos()
    if grupos:
        processar_grupos(grupos)
