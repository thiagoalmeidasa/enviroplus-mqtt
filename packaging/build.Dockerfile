# syntax=docker/dockerfile:1.7
ARG BUILDER_IMAGE
FROM ${BUILDER_IMAGE} AS build
ARG DEB_VERSION
ARG SUITE
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /work
COPY . .
RUN dch -v "${DEB_VERSION}" -D "${SUITE}" --force-distribution \
        "Automated build of ${DEB_VERSION}" \
 && ( mk-build-deps --install --remove --tool \
          "apt-get -y --no-install-recommends" debian/control \
      || ( apt-get update \
        && mk-build-deps --install --remove --tool \
            "apt-get -y --no-install-recommends" debian/control ) ) \
 && dpkg-buildpackage -us -uc -b \
 && mkdir -p /artifacts \
 && cp ../enviroplus-mqtt_*.deb /artifacts/

FROM scratch AS deb
COPY --from=build /artifacts/ /
