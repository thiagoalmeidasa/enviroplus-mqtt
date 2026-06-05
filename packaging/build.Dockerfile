# syntax=docker/dockerfile:1.7
ARG BUILDER_IMAGE
FROM ${BUILDER_IMAGE} AS build
ARG DEB_VERSION
ARG SUITE
# Optional extra PyPI index for pip (set to https://www.piwheels.org/simple
# for armhf so prebuilt wheels are used instead of compiling under QEMU).
# Empty by default — pip ignores an empty PIP_EXTRA_INDEX_URL.
ARG PIP_EXTRA_INDEX_URL=""
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
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
