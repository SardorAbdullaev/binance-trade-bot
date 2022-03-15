FROM python:3.8 as builder

WORKDIR /install
RUN apt-get update && apt-get install -y rustc

COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM python:3.8-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/lorcalhost/BTB-manager-telegram.git

COPY --from=builder /install /usr/local

COPY . /app/binance-trade-bot

WORKDIR /app/BTB-manager-telegram

CMD [ "python", "-m", "btb_manager_telegram"]
