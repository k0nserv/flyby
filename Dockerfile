FROM python:3.4-alpine
RUN apk add --update haproxy
WORKDIR /usr/src/app
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD . .
RUN pip install -e .
EXPOSE 5000
CMD ["flyby", "start"]