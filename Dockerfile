FROM alpine:3.13.7

RUN mkdir -p /usr/src/tap-outbrain
WORKDIR /usr/src/tap-taboola

RUN apk update
RUN apk upgrade
RUN apk add curl
RUN apk add python3
RUN pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache

ADD . /usr/src/tap-taboola

RUN pip3 install --upgrade .
RUN pip3 install target-stitch==0.7.3

CMD [ "/bin/sh", "-c", "/usr/src/tap-taboola/tap_taboola/__init__.py -c /usr/src/tap-taboola/config.json | target-stitch -c /usr/src/tap-taboola/persist.json" ]
