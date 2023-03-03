FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

RUN apt update && apt install -y build-essential curl && rm -rf /var/lib/apt/lists/*

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN rustup update

WORKDIR /DiscordBot
ADD requirements.txt /DiscordBot
RUN pip3 install -r requirements.txt

RUN rustup self uninstall -y
RUN apt purge -y build-essential curl && apt autoremove -y

COPY ./ /DiscordBot

CMD ["python3", "main.py"]