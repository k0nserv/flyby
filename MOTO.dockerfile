FROM python:3.4-alpine
RUN pip install moto
EXPOSE 80
CMD ["moto_server", "dynamodb2", "-p", "8000"]