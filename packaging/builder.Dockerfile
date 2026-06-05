ARG BASE_IMAGE=debian:bookworm-slim
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      debhelper \
      devscripts \
      dh-python \
      dh-virtualenv \
      dpkg-dev \
      equivs \
      fakeroot \
      git \
      libfreetype6-dev \
      libjpeg-dev \
      libsystemd-dev \
      pkg-config \
      python3 \
      python3-dev \
      python3-pip \
      python3-setuptools \
      python3-venv \
      python3-wheel \
      zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /work
