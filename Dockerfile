
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/home/app/.cache/huggingface

WORKDIR /app

# Actualizar pip
RUN pip install --no-cache-dir --upgrade pip

# Instalar PyTorch para CPU
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch>=2.6.0"

# Instalar el resto de las dependencias
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el backend
COPY . .

# Crear usuario sin privilegios
RUN groupadd --system app \
    && useradd --system --gid app --create-home app \
    && mkdir -p /home/app/.cache/huggingface /app/reports \
    && chown -R app:app /app /home/app

USER app

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
