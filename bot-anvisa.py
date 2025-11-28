# Standard Libraries --------
from datetime import datetime, timedelta
import re
import os
import json

# External Libraries ----------
from unidecode import unidecode
import psycopg2 as pg
import pandas as pd
import requests

# Configurações (definir no topo)
CONFIG_FILE = 'bot_anvisa_config.json'

# Funções de configuração
def carregar_config():
    """Carrega a configuração do arquivo JSON"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Garante que ultima_data_processada seja um inteiro
            if 'ultima_data_processada' in config:
                config['ultima_data_processada'] = int(config['ultima_data_processada'])
            return config
    else:
        # Configuração padrão
        config = {
            'ultima_pagina_processada': 0,
            'ultima_data_processada': int(datetime.now().strftime('%Y%m%d'))
        }
        salvar_config(config)
        return config

def salvar_config(config):
    """Salva a configuração no arquivo JSON"""
    # Faz uma cópia para não modificar o dicionário original
    config_to_save = config.copy()
    # Garante que os valores estão no formato correto
    config_to_save['ultima_data_processada'] = str(config['ultima_data_processada'])
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_to_save, f, indent=4)

# Funções principais
def RequestAnvisa(page, url, maximo_tentativa=3):
    print(f"Enviando request para Anvisa ({page}): ")

    tentativa = 0
    while tentativa < maximo_tentativa + 1:

        if tentativa != 0 & tentativa <= maximo_tentativa:
            print(f"Enviando request para Anvisa ({page}): Falhado: Tentando {tentativa}/{maximo_tentativa}.")

        try:

            request = requests.get(url, timeout=300)
            request_text = request.text
            text_normalizado = unidecode(request_text)

            print(f"Enviando request para Anvisa ({page}): Concluido.")

            return text_normalizado

        except:
            print(f"Enviando request para Anvisa ({page}): Falhado: ")
            tentativa += 1

    print(f"Enviando request para Anvisa ({page}): Falhado: Cancelado.")
    print("-----------------------------")

    return None

def VerificarAquivos(request, numero_page_final):
        
    if request is not None:
        mensagem = 'Atualmente não existem itens nessa pasta'
        mensagem_normalizado = unidecode(mensagem)

        print(f"Verificando Arquivos in Page ({numero_page_final}): ")

        if mensagem_normalizado in request:
            print(f"Verificando Arquivos in Page ({numero_page_final}): None.")
            print("-----------------------------")
            return True
        else:
            print(f"Verificando Arquivos in Page ({numero_page_final}): True.")
            return False
            
    return True

def ObterLinkDownloadXls(contem, numero_page_final):
    print(f"Obtendo o Link do Arquivo xlsx ({numero_page_final}): ")

    if contem:
        link_xls = contem.group(0)
        # Remover "/view" do final do link
        link_xls_limpo = link_xls.replace('/view', '')
        print(f"Obtendo o Link do Arquivo xlsx ({numero_page_final}): Link Encontrado com Sucesso.")
        print(f"Link limpo: {link_xls_limpo}")
        return link_xls_limpo
    else:
        print(f"Obtendo o Link do Arquivo xlsx ({numero_page_final}): Link Encontrado sem Sucesso.")
        print("-----------------------------")
        return None

def ProcurarArquivosXls(request, numero_page_final, data=None):
    
    if data is None:
        print(f"Procurando qualquer arquivo XLSX ({numero_page_final}): ")
        padrao = r'https?://[^\s]*xls_conformidade_site_\d+_[^\s]*\.xlsx'
    else:
        print(f"Procurando Data nos Arquivos ({numero_page_final}): Data {data}.")
        padrao = rf'https?://[^\s]*xls_conformidade_site_{data}[^\s]*\.xlsx'
    
    padrao_normalizado = unidecode(padrao)
    contem = re.search(padrao_normalizado, request)

    if contem:
        if data:
            print(f"Procurando Data nos Arquivos ({numero_page_final}): True: Data {data}.")
        else:
            print(f"Procurando qualquer arquivo XLSX ({numero_page_final}): True.")
        return False, contem 
    else:
        if data:
            print(f"Procurando Data nos Arquivos ({numero_page_final}): None: Data {data}.")
        else:
            print(f"Procurando qualquer arquivo XLSX ({numero_page_final}): None.")
        print("-----------------------------")
        return True, 0

def ProcessarTabelaListaAnvisa(link_xls, data_atual):
    print('Leitura do arquivo xlsx: ')
    
    # Usar openpyxl para .xlsx
    try:
        dt_table = pd.read_excel(link_xls, engine='openpyxl')
        print('Leitura do arquivo xlsx: Concluída com openpyxl.')
    except Exception as e:
        print(f"Openpyxl falhou: {e}")
        # Fallback para xlrd
        try:
            dt_table = pd.read_excel(link_xls, engine='xlrd')
            print('Leitura do arquivo xlsx: Concluída com xlrd.')
        except Exception as e2:
            raise Exception(f"Todos os engines falharam: {e2}")
    
    print("Encontrando a linha inicial: ")
    index = dt_table.isin(['SUBSTÂNCIA']).any(axis=1).idxmax()
    colunas = dt_table.iloc[index,:].tolist()
    dt_table = dt_table.iloc[(index+1):, :]
    dt_table.columns = colunas
    print("Encontrando a linha inicial: Concluída.")

    print('Extraindo EAN_2 e EAN_3 para a coluna EAN_1:')
    dt_ean2 = dt_table[dt_table['EAN 2'].str.contains('-') == False]
    dt_ean2 = dt_ean2.drop(['EAN 1', 'EAN 3'], axis=1)
    dt_ean2 = dt_ean2.rename(columns={'EAN 2': 'EAN 1'})
    dt_ean3 = dt_table[dt_table['EAN 3'].str.contains('-') == False]
    dt_ean3 = dt_ean3.drop(['EAN 1', 'EAN 2'], axis=1)
    dt_ean3 = dt_ean3.rename(columns={'EAN 3': 'EAN 1'})
    dt_table = dt_table.drop(['EAN 2', 'EAN 3'], axis=1)
    dt_table = pd.concat([dt_table, dt_ean2, dt_ean3], ignore_index=True)
    print('Extraindo EAN_2 e EAN_3 para a coluna EAN_1: Concluída.')

    print('Padronizando todas as colunas da tabela lista_anvisa: ')
    for coluna in dt_table.columns:
        new_nome = PadronizarColunas(coluna)
        dt_table = dt_table.rename(columns={coluna: new_nome})
    print('Padronizando todas as colunas da tabela lista_anvisa: Concluída.')

    print('Padronizando todas as células da tabela lista_anvisa: ')
    for index, linha in dt_table.iterrows():
        for coluna in dt_table.columns:
            palavra_antiga = linha[coluna]
            dt_table.loc[index, coluna] = PadronizarLinhas(palavra_antiga)
    print('Padronizando todas as células da tabela lista_anvisa: Concluída.')

    print('Adicionando coluna para data de publicação da lista_anvisa: ')
    dt_table['date_time'] = data_atual
    print('Adicionando coluna para data de publicação da lista_anvisa: Concluída.')
    print()

    return dt_table

def PadronizarColunas(string):
    string = unidecode(string)
    string = string.replace(' ', '_')
    string = re.sub(r'[^a-zA-Z0-9_]', '', string)
    string = string.lower()
    return string

def PadronizarLinhas(string):
    new_string = string
    if type(string) == str:
        string = unidecode(string)
        new_string = string.upper()
    return new_string

def obter_colunas_existentes(cursor, tabela):
    query = f"SELECT column_name FROM information_schema.columns WHERE table_name='{tabela}'"
    cursor.execute(query)
    colunas_existentes = cursor.fetchall()
    return [coluna[0] for coluna in colunas_existentes]

def alterar_tabela(cursor, dt_table, tabela):
    colunas_existentes = obter_colunas_existentes(cursor, tabela)
    for coluna in dt_table.columns:
        if coluna not in colunas_existentes:
            alter_table = f"ALTER TABLE {tabela} ADD COLUMN {coluna} TEXT"
            cursor.execute(alter_table)
            print(f"Coluna {coluna} adicionada.")

def validar_colunas(dt_table, colunas_existentes):
    colunas_invalida = [col for col in dt_table.columns if col not in colunas_existentes]
    if colunas_invalida:
        raise ValueError(f"As seguintes colunas não existem na tabela: {', '.join(colunas_invalida)}")
    return [col for col in dt_table.columns if col in colunas_existentes]

def salvar_arquivo_local(dt_table, data_processamento, pagina):
    """Salva o DataFrame como arquivo XLSX localmente em caso de erro no banco"""
    try:
        pasta_backup = 'backup_anvisa'
        if not os.path.exists(pasta_backup):
            os.makedirs(pasta_backup)
        
        nome_arquivo = f"lista_anvisa_{data_processamento}_pagina_{pagina}.xlsx"
        caminho_completo = os.path.join(pasta_backup, nome_arquivo)
        
        dt_table.to_excel(caminho_completo, index=False, engine='openpyxl')
        print(f"Arquivo salvo localmente: {caminho_completo}")
        return True
    except Exception as e:
        print(f"Erro ao salvar arquivo localmente: {e}")
        return False

def SalvarnoBanco(dt_table, data_processamento, pagina):
    try:
        # Conectar ao banco de dados (substitua com suas credenciais)
        conn = pg.connect(host="xx.xx.xx.xx", dbname="xxxxxxxxxxxx", user="xxxxxxxxxxxx", port="0000", password="")
        cursor = conn.cursor()

        tabela = 'lista_anvisa_robo'

        colunas_existentes = obter_colunas_existentes(cursor, tabela)

        create_table = f"""
        CREATE TABLE IF NOT EXISTS {tabela} (
            id SERIAL PRIMARY KEY
        );
        """
        cursor.execute(create_table)
        conn.commit()

        alterar_tabela(cursor, dt_table, tabela)
        conn.commit()

        colunas_validas = validar_colunas(dt_table, colunas_existentes)

        insert_table = f"INSERT INTO {tabela} ({', '.join(colunas_validas)}) VALUES "
        valores_lista = []

        for i in range(len(dt_table)):
            values = []
            for coluna in colunas_validas:
                v = dt_table.loc[i, coluna]
                if pd.isna(v) or v == 'null':
                    values.append('NULL')
                else:
                    values.append("'" + str(v).replace("'", '') + "'")
            valores_lista.append(f"({', '.join(values)})")

        insert_table += ', '.join(valores_lista) + ';'

        cursor.execute(insert_table)
        conn.commit()

        cursor.close()
        conn.close()
        
        print("Dados salvos no banco de dados com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")
        print("Tentando salvar localmente...")
        
        if salvar_arquivo_local(dt_table, data_processamento, pagina):
            print("Backup local realizado com sucesso!")
        else:
            print("Falha ao salvar backup local!")
            
        return False

def encontrar_arquivo_mais_recente_global():
    """Procura em todas as páginas pelo arquivo mais recente"""
    print("🔍 PROCURANDO ARQUIVO MAIS RECENTE EM TODAS AS PÁGINAS...")
    
    url_base = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/arquivos?b_start:int="
    data_mais_recente = None
    link_mais_recente = None
    pagina_mais_recente = 0
    
    # Verificar páginas de 0 até 600 (incrementando de 20 em 20)
    for pagina in range(0, 601, 20):
        print(f"Verificando página {pagina}...")
        
        # Fazer request para a página
        request = RequestAnvisa(pagina, url_base + str(pagina))
        
        # Verificar se a página tem arquivos
        if VerificarAquivos(request, pagina):
            print(f"Página {pagina}: Sem arquivos. Parando busca.")
            break
        
        # Buscar todas as datas no formato AAAAMMDD
        padrao_xlsx = r'https?://[^\s]*xls_conformidade_site_(\d{8})[^\s]*\.xlsx'
        matches = re.findall(padrao_xlsx, request)
        
        if matches:
            datas = [int(data) for data in matches]
            data_atual_pagina = max(datas)
            
            # Atualizar o mais recente encontrado
            if data_mais_recente is None or data_atual_pagina > data_mais_recente:
                data_mais_recente = data_atual_pagina
                
                # Buscar o link correspondente
                padrao_link = rf'https?://[^\s]*xls_conformidade_site_{data_atual_pagina}[^\s]*\.xlsx'
                link_match = re.search(padrao_link, request)
                if link_match:
                    link_mais_recente = link_match.group(0).replace('/view', '')
                    pagina_mais_recente = pagina
                    print(f"  → Novo arquivo mais recente encontrado: {data_mais_recente} na página {pagina}")
    
    if data_mais_recente and link_mais_recente:
        print(f"🎯 ARQUIVO MAIS RECENTE GLOBAL: Data {data_mais_recente}")
        print(f"📄 Encontrado na página: {pagina_mais_recente}")
        print(f"🔗 Link: {link_mais_recente}")
        return data_mais_recente, link_mais_recente, pagina_mais_recente
    else:
        print("❌ Nenhum arquivo recente encontrado em nenhuma página")
        return None, None, None

def executar_bot_anvisa():
    """Função principal do bot ANVISA com busca global pelo mais recente"""
    
    # Carregar configuração
    config = carregar_config()
    ultima_pagina = config.get('ultima_pagina_processada', 0)
    ultima_data_processada = config.get('ultima_data_processada', 0)
    
    print(f"📊 Último processamento:")
    print(f"   Página: {ultima_pagina}")
    print(f"   Data: {ultima_data_processada}")
    print("Buscando arquivo mais recente globalmente...")
    
    # Buscar globalmente pelo arquivo mais recente
    data_mais_recente, link_mais_recente, pagina_mais_recente = encontrar_arquivo_mais_recente_global()
    
    if data_mais_recente is None:
        print("❌ Nenhum arquivo recente encontrado.")
        return False
    
    # Verificar se já processamos este arquivo
    if data_mais_recente <= ultima_data_processada:
        print(f"✅ Arquivo mais recente ({data_mais_recente}) já foi processado anteriormente ({ultima_data_processada})")
        return False
    
    print(f"🎯 NOVO ARQUIVO ENCONTRADO: Data {data_mais_recente}")
    print(f"📄 Página: {pagina_mais_recente}")
    print(f"🔗 Link: {link_mais_recente}")
    
    # Processar o novo arquivo
    try:
        lista_anvisa = ProcessarTabelaListaAnvisa(link_mais_recente, data_mais_recente)
        
        # Tenta salvar no banco
        sucesso_banco = SalvarnoBanco(lista_anvisa, data_mais_recente, pagina_mais_recente)
        
        # Se falhar ao salvar no banco, tenta salvar localmente
        if not sucesso_banco:
            sucesso_local = salvar_arquivo_local(lista_anvisa, data_mais_recente, pagina_mais_recente)
            if sucesso_local:
                print("Backup local realizado com sucesso!")
            else:
                print("Falha ao salvar localmente!")
                return False
        
        # Atualiza a configuração independentemente de ter salvado no banco ou localmente
        config['ultima_pagina_processada'] = pagina_mais_recente
        config['ultima_data_processada'] = data_mais_recente
        salvar_config(config)
        
        if sucesso_banco:
            print(f"✅ Página {pagina_mais_recente} processada com sucesso! Data: {data_mais_recente}")
        else:
            print(f"⚠️ Página {pagina_mais_recente} processada com salvamento local! Data: {data_mais_recente}")
        
        return True
            
    except Exception as ex:
        print(f'❌ Erro ao processar página {pagina_mais_recente}: {ex}')
        return False

# Execução principal
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=== BOT ANVISA - PROCESSAMENTO AUTOMÁTICO ===")
    
    # Executar o bot
    sucesso = executar_bot_anvisa()
    
    if sucesso:
        print("Processamento concluído com sucesso!")
    else:
        print("Nenhum novo arquivo para processar.")
    
    print("=== FIM DO PROCESSAMENTO ===")