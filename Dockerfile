FROM python:3.4-alpine
RUN apk add --update haproxy
WORKDIR /usr/src/app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN pip install .
EXPOSE 5000
CMD ["flyby", "start"]