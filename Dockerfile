FROM python:3.12-slim

WORKDIR /app

# Copiar arquivos de requisitos primeiro
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do bot
COPY . .

# Criar os diretórios necessários
RUN mkdir -p cogs
RUN mkdir -p imagens

# Comando para iniciar o bot
CMD ["python", "main.py"]