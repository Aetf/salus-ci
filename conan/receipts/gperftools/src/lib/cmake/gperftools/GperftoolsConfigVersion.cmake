# assume the file is in lib/cmake/gperftools/GperftoolsConfigVersion.cmake
get_filename_component(Gperftools_PKGCONFIG_DIR "${CMAKE_CURRENT_LIST_DIR}/../../pkgconfig" ABSOLUTE)

find_package(PkgConfig)
set(ENV{PKG_CONFIG_PATH} ${Gperftools_PKGCONFIG_DIR})
set(ENV{PKG_CONFIG_LIBDIR} ${Gperftools_PKGCONFIG_DIR})
pkg_check_modules(PC_tcmalloc QUIET libtcmalloc)

set(PACKAGE_VERSION PC_tcmalloc_VERSION)

# Check whether the requested PACKAGE_FIND_VERSION is compatible
if("${PACKAGE_VERSION}" VERSION_LESS "${PACKAGE_FIND_VERSION}")
  set(PACKAGE_VERSION_COMPATIBLE FALSE)
else()
  set(PACKAGE_VERSION_COMPATIBLE TRUE)
  if ("${PACKAGE_VERSION}" VERSION_EQUAL "${PACKAGE_FIND_VERSION}")
    set(PACKAGE_VERSION_EXACT TRUE)
  endif()
endif()
