FROM alpine:3.13

LABEL \
    maintainer="Frank LENORMAND <lenormf@gmail.com>" \
    description="Run the MediaSurf gallery" \
    source="https://github.com/lenormf/mediasurf"

ARG RELEASE="master"

EXPOSE 8080

VOLUME /media

WORKDIR /root

RUN \
    apk update \
    && apk add python3 ffmpeg zlib jpeg \
               gcc musl-dev python3-dev zlib-dev jpeg-dev \
               py3-pip unzip make

RUN \
    wget -O mediasurf.zip https://github.com/lenormf/mediasurf/archive/"${RELEASE}".zip \
    && unzip mediasurf.zip -d mediasurf-build

RUN \
    cd mediasurf-build/mediasurf-* \
    && pip3 install -r requirements.txt \
    && make install

RUN \
    rm -r mediasurf.zip mediasurf-build \
    && apk del \
               gcc musl-dev python3-dev zlib-dev jpeg-dev \
               unzip make \
    && rm -rf /var/cache/apk/*

ENTRYPOINT ["mediasurf", "-d", "-H", "0.0.0.0", "/media"]
