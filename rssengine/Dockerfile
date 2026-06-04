FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Pre-download common Hugging Face model into a persistent cache to speed container startup.
# The HF cache directory is set by HF_HOME and will be mounted from docker-compose (see compose file).
ENV HF_HOME=/cache/huggingface
ENV HF_HUB_DISABLE_PROGRESS_BARS=1

# Download the sentiment model at build time so containers start faster.
RUN python - <<'PY'
from transformers import AutoTokenizer, AutoModelForSequenceClassification
model = 'apriandito/indobert-binary-sentiment-classifier'
AutoTokenizer.from_pretrained(model)
AutoModelForSequenceClassification.from_pretrained(model)
print('HF model predownload complete')
PY

COPY rssengine ./rssengine

USER app

CMD ["python", "-m", "rssengine.main"]
