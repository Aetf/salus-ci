# Salus CI Supporting

[![Build Status](https://travis-ci.com/Aetf/salus-ci.svg?branch=master)](travis-ci)

Various supporting libraries and scripts for [Salus](https://github.com/SymbioticLab/Salus).

## Conan repository

This conan channel provides various dependencies not available in conan-center.
To setup, run

```bash
conan remote add <REMOTE> https://api.bintray.com/conan/symbioticlab/salus-conan
```

and replace `<REMOTE>` with a name that identifies the repository (for example: "salus-conan").

### Packages

- protobuf (adapted from [conan-center-index](https://github.com/conan-io/conan-center-index))
- gperftools

## Conan builder images

This repo provides additional `ppc64le` architecture builder dockerfiles that can be used alongside
[official images](https://github.com/conan-io/conan-docker-tools).
Prebuilt images are available at [Salus's container
registry](https://gitlab.com/Salus/Salus/container_registry
).

See this repo's config for how to use them
with `conan-package-tools`.

[travis-ci]: https://travis-ci.com/Aetf/salus-ci
