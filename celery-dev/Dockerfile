FROM python:3.9-bookworm

WORKDIR /code
COPY . .

RUN pip install --default-timeout=100 -r requirements.txt
RUN pip install gunicorn

EXPOSE 5004