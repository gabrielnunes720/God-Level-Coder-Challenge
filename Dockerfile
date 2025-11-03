# Usa uma imagem Python oficial como base
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o requirements.txt (da raiz) para dentro do container
# Este é o requirements.txt com 'faker' e 'psycopg2'
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o script de geração para dentro do container
COPY generate_data.py .

# O comando que o script vai rodar já está definido no docker-compose.yml