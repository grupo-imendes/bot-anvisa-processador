# Bot ANVISA - Processamento de Preços de Medicamentos

Este projeto implementa um bot automatizado para coleta e processamento de dados de preços de medicamentos da ANVISA (Agência Nacional de Vigilância Sanitária).

## 📋 Descrição

O Bot ANVISA é responsável por:

- Buscar automaticamente os arquivos mais recentes de preços de medicamentos no portal da ANVISA
- Processar e padronizar os dados contidos nos arquivos XLSX
- Armazenar os dados processados em um banco de dados PostgreSQL
- Manter backup local dos arquivos em caso de falha na conexão com o banco

## 🚀 Funcionalidades

- **Busca Inteligente**: Procura globalmente pelo arquivo mais recente em todas as páginas do portal
- **Processamento Automático**: Identifica e processa automaticamente novos arquivos
- **Resiliência**: Múltiplas tentativas de requisição e fallback para salvamento local
- **Padronização**: Normaliza colunas e dados para consistência
- **Configuração Persistente**: Mantém histórico do último processamento

## 🛠️ Tecnologias Utilizadas

- Python 3.x
- Pandas - Processamento de dados
- Psycopg2 - Conexão com PostgreSQL
- Requests - Requisições HTTP
- Unidecode - Normalização de texto
- Openpyxl/xlrd - Leitura de arquivos Excel

## 📦 Dependências

```bash
pip install pandas psycopg2-binary requests unidecode openpyxl xlrd
```

## ⚙️ Configuração

### Arquivo de Configuração

O bot utiliza um arquivo `bot_anvisa_config.json` para armazenar:

- `ultima_pagina_processada`: Última página processada
- `ultima_data_processada`: Data do último arquivo processado

### Banco de Dados

Configure as credenciais do PostgreSQL na função `SalvarnoBanco()`:

```bash
conn = pg.connect(
    host="xx.xx.xx.xx",
    dbname="xxxxxxxxxxxx", 
    user="xxxxxxxxxxxx",
    port="0000",
    password=""
)
```

## 🎯 Como Usar

### Execução Simples

```bash
python bot_anvisa.py
```

## Fluxo de Execução

1. **Busca Global**: Varre todas as páginas do portal ANVISA (0-600)
2. **Identificação**: Encontra o arquivo XLSX mais recente
3. **Verificação**: Compara com o último processamento
4. **Processamento**: Se for novo, processa e padroniza os dados
5. **Armazenamento**: Salva no banco de dados ou localmente

## 📊 Estrutura de Dados

- **Tabela Principal**: `lista_anvisa_robo`
- Colunas dinâmicas baseadas na estrutura do arquivo ANVISA
- Padronização automática de nomes de colunas
- Campo `date_time` com data de publicação

## Processamento de Dados

- Extração de múltiplos códigos EAN (EAN 1, EAN 2, EAN 3)
- Normalização de caracteres especiais
- Padronização para maiúsculas

## 🔧 Funcionalidades Avançadas

- Busca Global

```bash

encontrar_arquivo_mais_recente_global()
```

## Fallback Local
```bash
salvar_arquivo_local()
```

### salvar_arquivo_local()

**Local de salvamento:** `backup_anvisa/`

**Características:**
- Nomeação automática com data e página
- Garante que dados não sejam perdidos em caso de falhas
- Estrutura organizada por data de processamento

## Tolerância a Falhas

**Sistema robusto com:**
- Até 3 tentativas de requisição para cada operação
- Múltiplos engines para leitura de Excel (openpyxl, xlrd)
- Validação de estrutura de tabela antes do processamento
- Fallback automático para backup local

## 📁 Estrutura de Arquivos
bot-anvisa/
├── bot-anvisa.py          # Script principal
├── bot_anvisa_config.json # Configurações persistentes
├── backup_anvisa/         # Backup de arquivos processados
│   └── lista_anvisa_YYYYMMDD_pagina_X.xlsx
└── README.md

# 🐛 Solução de Problemas

## Problemas Comuns

### Falha de Conexão com Banco
- **Solução**: Dados são salvos localmente como backup
- **Ação**: Verifique credenciais do PostgreSQL

### Arquivo XLSX Corrompido
- **Solução**: O bot tenta múltiplos engines (openpyxl, xlrd)
- **Ação**: Verifique o formato do arquivo da ANVISA

### Mudança na Estrutura do Portal
- **Solução**: Atualize os padrões de regex na busca
- **Ação**: Verifique a URL base do portal

## Logs e Debug
- Logs detalhados de cada etapa do processo
- Identificação de páginas e datas processadas
- Mensagens de erro descritivas

# 🔄 Manutenção

## Atualizações Regulares
- Execute diariamente para capturar novos arquivos
- Monitore logs para detectar mudanças no portal

## Customização
- Modifique `CONFIG_FILE` para mudar localização da configuração
- Ajuste `maximo_tentativa` para mais/menos tentativas de requisição

# 📄 Licença
Este projeto é para uso interno. Verifique os termos de uso dos dados da ANVISA.

# 🤝 Contribuições
Para reportar problemas ou sugerir melhorias, abra uma issue no repositório do projeto.

---

**Nota**: Este bot foi desenvolvido para automatizar o processo de coleta de dados de preços de medicamentos da ANVISA, garantindo eficiência e confiabilidade no processamento.