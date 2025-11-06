# Execução no Streamlit Cloud

Este guia descreve o que é necessário para rodar este projeto no Streamlit Cloud.

## 1) Dependências

- O arquivo `requirements.txt` já está incluído e lista as dependências necessárias:
  - `langgraph>=1.0.2`
  - `python-dotenv>=1.2.1`
  - `streamlit>=1.51.0`

Se você adicionar novas bibliotecas, lembre-se de atualizar `requirements.txt`.

## 2) Arquivo principal (entrypoint)

- No Streamlit Cloud, selecione `app.py` como arquivo principal ao criar o app.

## 3) Portas e configuração de servidor

- O Cloud gerencia porta/host automaticamente. O arquivo `.streamlit/config.toml` define `port=5000`, mas isso não impede a execução. Se preferir, você pode remover a linha `port = 5000`.

## 4) Segredos/Variáveis de ambiente

- Este projeto utiliza um serviço externo para classificar os tickets. Defina um segredo:
  - `OPENAI_API_KEY` (recomendado) ou `MODEL_API_KEY`.
- No Streamlit Cloud, use a aba "Secrets" para cadastrar a chave (ela ficará disponível como variável de ambiente durante a execução).

## 5) Dados de exemplo

- O arquivo `data/tickets.json` acompanha dados de exemplo. Você pode editar para personalizar os tickets.

## 6) Versão de Python

- O Streamlit Cloud usa uma versão recente de Python. Este projeto foi escrito para Python 3.11, mas não depende de recursos específicos dessa versão. Caso precise fixar versão, você pode adicionar um arquivo `runtime.txt` (por ex.: `python-3.11`).

## 7) Teste local antes do deploy

- Rode localmente:
  - `pip install -r requirements.txt`
  - `streamlit run app.py`

## 8) Passos rápidos no Streamlit Cloud

1. Faça o push do repositório para GitHub.
2. No Streamlit Cloud, crie um novo app e aponte para `app.py`.
3. Aguarde a instalação das dependências.
4. O app deve subir automaticamente sem configuração extra.
