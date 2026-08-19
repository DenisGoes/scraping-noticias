# Imagem base
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretorio de trabalho
WORKDIR /app

# Dependencias do sistema
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Dependencias python
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Instala os browsers do Playwright
RUN playwright install --with-deps chromium

# Código da aplicação
COPY . .

# Criando usuario
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
    
USER appuser

# Porta da aplicação
EXPOSE 8000

# Comando para produção
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]