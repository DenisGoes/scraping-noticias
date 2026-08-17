# 1 - Imagem base
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 2 - Diretorio de trabalho
WORKDIR /app

# 3 - Dependencias do sistema
RUN apt-get update && apt-get install -y \ 
    <dependencias-do-sistema> \
    ** rm -rf /var/lib/apt/lists/*

# 4 - Dependencias python
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# 5 - Código da aplicação
COPY . .

# 6 - Criando usuario
RUN useradd --create-home appuser
USER appuser

# 7 - Porta da aplicação
EXPOSE 8000

# 8 - Comando para produção
CMD [ "uvicorn", "backend.main.app", "--host", "0.0.0.0", "--port", "8000" ]