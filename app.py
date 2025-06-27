from flask import Flask, jsonify
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Isso permite requisições do frontend

# Configuração do Google Sheets
SCOPE = ["https://www.googleapis.com/auth/drive", 
         "https://www.googleapis.com/auth/spreadsheets",
         "https://spreadsheets.google.com/feeds"]

# Credenciais da conta de serviço
CREDENTIALS = {
    "type": "service_account",
    "project_id": "accounttocopypaste",
    "private_key_id": "412416fd2dc54398f64bcce874e04d3e944cd524",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCnbEsvS6qj1Cxw\ngKW3eWZkp2FRtmfgn4doIH2Yi85gYrgbzxnEUGCmJAREdqjN/O5WALl42fZduxJS\nk1LUhvUfehR9vevFbfddyInIBXqZDEqZ0v9b5CR9Qqw0gI2+68jnIk/U0mZ4XBUZ\ntdcwZmE7eOCKy+xp2Zj+C6Z5N2EgvdmToOdEg7kXaLuFsp+Qy1r3b15kZywL+Qqv\nBaSgDXQ7OB3mlAAkLivXax1m+7awsKF5h1Ep7y5K2BI12z0Yu5xri+Dhyfi1xQh/\n+cJSYfSZmUDscjFBxYngdkf015XzBUhq8VrteBGBd43qouqhNF8EgsREpCmf2dUD\nNx9z4Lk/AgMBAAECggEAKWfO8FN2UC4ZD3nBgi6z9BCxMNQ7vIG3qzjd1uw8jfnc\nLoR5iuOWA4DEzWnLNaZoCz0CobDGDUhGr8Vfps/5r18x0ic2OA2KL9d4u88fEtrH\nWGOmY8N4gsIKdLGWXLFTblY+CBRA42NilIk0PvQS9/JdFfZ48XSvMaUP9sqLat0i\njzXIVRVkhKySuQKqRyVWaxwEr+h1rRDmEzQhrl7JJqZTP5wFN4VQW+7fw4AQXr1r\nyKN50SCLMi+fMn72s325ios1kkVqB9vC4U7xammV5BnpRuccArnbfLhF4eJtx6kZ\nz1agCr51H/pLmVDyaUWTt8Zf9ELdBZNwrsDlCmHIgQKBgQDI0dD+09TYkYABzZ3b\nxQrTKIzrq49BuqhOg3XWUSe75S4At2ulaJvdZ2dKRe9P+qjFOZV17+UhjBqa8anj\nI0hoZnUdrNa1hneLPQIJGJvbRWp3T8LVpsDkCTtlqUEwx7NJWpECEdV28eWHpc4w\naz5IU4KoHDlINp88ArUTJLLR9QKBgQDVbUYPL8V4PuEG9inw4HsSipz0bdUMGBkW\nk8WOlaZsLuCDL+1lSnETiQu6EqV8NfBxwtzXnbKrJ3IiktDr/TbZ7D9yoXGtnuk+\noncMeUi/ZiDt/Xf3oLznsgWFIsTmZljL4d622KBU1hZDnxrL/fwziu8OV+IkP0Vd\nlFI5nq054wKBgQDAhMUDRzjJ1dMN53zqb2ANRtayJ+pSbQtlGYoiR/L7op4TecPs\n8vhZrQPMpHbkCb06NhYe1jinjJUE7aCca/rCe1bTeBruM1bvWTFWXw0rjMSgVQrH\nn/FTq7YRo80nYotySyyw+z/Vo9kTzdR5fpZa6BRd7ZDMtfC5qy7Eh24W8QKBgF4+\n3s0d/0lWGvCEC4k+15occ6rMRWQN0CZUIs0P8GmdWa8UnvQ3py9FOVR1n3X2K7NQ\npUzhamCCDriNtIxBSNN6q5nnCNfucHkkLQXpGOLMKoZtg2hqJoD5784WyHQlhdii\naUK87jAISdSaka66/X+VPnNLA6WV+v+T26tuEniZAoGAbBKQRdyJQ2pxUKyt2+GL\nQh3xh2LR0Se6z2wR8Sx2SpOoKU4VadWrovxU2qwk+qG1pqC0lAHsK1LiRSEdcZdL\nEsnHMp0tnkMkre6LqXLTb8QIR0Qj4HiEVxkUCPwuX5mgkksixWfzmYjp2uqoTrtK\nnwapi2gvK+9LZDORytpbYN4=\n-----END PRIVATE KEY-----\n",
    "client_email": "accountcopypastebot@accounttocopypaste.iam.gserviceaccount.com",
    "client_id": "115883670061446057641",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/accountcopypastebot%40accounttocopypaste.iam.gserviceaccount.com",
}

# ID da planilha
SPREADSHEET_ID = '1f-7STdKAcA9NfDT7ZrRIaDLpKO1FD1bZkOKaDrr7MV8'
WORKSHEET_NAME = 'PRODUTOS'

def get_google_sheets_data():
    try:
        # Autenticação usando as credenciais embutidas
        creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS, SCOPE)
        client = gspread.authorize(creds)
        
        # Abre a planilha
        sheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet(WORKSHEET_NAME)
        
        # Obtém todos os valores
        data = worksheet.get_all_values()
        
        if not data:
            return []

        # Converte para DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Verifica se as colunas necessárias existem
        required_columns = ['NOME', 'DESCRICAO', 'CATEGORIA']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Colunas faltando na planilha: {missing_columns}")
            return []

        # Converte para lista de dicionários
        produtos = []
        for _, row in df.iterrows():
            produto = {
                'nome': row['NOME'],
                'descricao': row['DESCRICAO'],
                'categoria': row['CATEGORIA'],
                'imagem': row['IMAGEM'] if 'IMAGEM' in row else 'https://via.placeholder.com/150/0e8fd8/ffffff?text=Produto'
            }
            produtos.append(produto)
        
        logger.debug(f"Total de produtos encontrados: {len(produtos)}")
        return produtos
    except Exception as e:
        logger.error(f"Erro ao acessar Google Sheets: {str(e)}")
        return []

@app.route('/api/produtos')
def get_produtos():
    logger.debug("Recebida requisição para /api/produtos")
    produtos = get_google_sheets_data()
    return jsonify(produtos)

if __name__ == '__main__':
    logger.info("Iniciando servidor Flask...")
    app.run(debug=True) 