FROM python:3.4-alpine

ARG GITSHA="VCS ref not found"
ARG BUILDDATE="Build date not found"
LABEL org.label-schema.vendor="Skyscanner" \
      org.label-schema.url="https://github.com/Skyscanner/flyby" \
      org.label-schema.name="Flyby" \
      org.label-schema.license="Apache-2.0" \
      org.label-schema.vcs-url="https://github.com/Skyscanner/flyby" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.description="Flyby is a simple distributed HAProxy layer used for load balancing our ECS shared cluster." \
      org.label-schema.vcs-ref=$GITSHA \
      org.label-schema.build-date=$BUILDDATE

RUN apk update && \
    apk add --update ca-certificates && \
    apk add --update haproxy && \
    update-ca-certificates

WORKDIR /usr/src/app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN pip install -e .
EXPOSE 5000
CMD ["flyby", "start"]