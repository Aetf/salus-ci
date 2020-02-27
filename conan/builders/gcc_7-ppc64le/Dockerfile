FROM conanio/gcc7

LABEL maintainer="Aetf <aetf@unlimited-code.works>"

ENV CC=powerpc64le-linux-gnu-gcc-7 \
    CXX=powerpc64le-linux-gnu-g++-7 \
    CMAKE_C_COMPILER=powerpc64le-linux-gnu-gcc-7 \
    CMAKE_CXX_COMPILER=powerpc64le-linux-gnu-g++-7 \
    STRIP=powerpc64le-linux-gnu-strip \
    RANLIB=powerpc64le-linux-gnu-ranlib \
    AS=powerpc64le-linux-gnu-as \
    AR=powerpc64le-linux-gnu-ar \
    LD=powerpc64le-linux-gnu-ld \
    FC=powerpc64le-linux-gnu-gfortran-7

COPY ppc64el.list /etc/apt/sources.list.d/ppc64el.list

RUN sudo dpkg --add-architecture ppc64el \
    && sudo sed -i 's/deb\s/deb \[arch=amd64,i386\] /' /etc/apt/sources.list \
    && sudo apt-get -qq update \
    && sudo apt-get -qq install -y --force-yes --no-install-recommends \
       ".*7.*powerpc64le-linux-gnu.*" \
    && sudo update-alternatives --install /usr/bin/powerpc64le-linux-gnu-gcc powerpc64le-linux-gnu-gcc /usr/bin/powerpc64le-linux-gnu-gcc-7 100 \
    && sudo update-alternatives --install /usr/bin/powerpc64le-linux-gnu-g++ powerpc64le-linux-gnu-g++ /usr/bin/powerpc64le-linux-gnu-g++-7 100 \
    && sudo update-alternatives --install /usr/bin/powerpc64le-linux-gnu-gcov powerpc64le-linux-gnu-gcov /usr/bin/powerpc64le-linux-gnu-gcov-7 100 \
    && sudo update-alternatives --install /usr/bin/powerpc64le-linux-gnu-gcov-dump powerpc64le-linux-gnu-gcov-dump /usr/bin/powerpc64le-linux-gnu-gcov-dump-7 100 \
    && sudo update-alternatives --install /usr/bin/powerpc64le-linux-gnu-gcov-tool powerpc64le-linux-gnu-gcov-tool /usr/bin/powerpc64le-linux-gnu-gcov-tool-7 100 \
    && sudo rm -rf /var/lib/apt/lists/* \
    && pip install -q --no-cache-dir conan conan-package-tools --upgrade \
    && conan profile new default --detect \
    && conan profile update settings.arch=ppc64le default
