FROM docker.m.daocloud.io/library/python:3.13-slim

WORKDIR /app/frontend

COPY frontend/ ./

EXPOSE 80

CMD ["python", "-m", "http.server", "80", "--bind", "0.0.0.0"]
