# 1. Usar una imagen oficial de Python ligera
FROM python:3.10-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /home/user/app

COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user:user . .

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:server"]