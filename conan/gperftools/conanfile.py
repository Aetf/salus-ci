import os
from conans import ConanFile, AutoToolsBuildEnvironment, tools


class GperftoolsConan(ConanFile):
    name = "gperftools"
    version = "2.7"
    license = "BSD-3-Clause"
    url = "https://github.com/Aetf/salus-ci"
    homepage = "https://github.com/gperftools/gperftools"
    description = ("The fastest malloc we’ve seen; works particularly well with threads and STL."
                   "Also: thread-friendly heap-checker, heap-profiler, and cpu-profiler.")
    settings = "os", "compiler", "build_type", "arch"
    short_paths = True

    exports_sources = 'src/FindGperftools.cmake'

    options = {
        "shared": [True, False]
    }
    default_options = {
        "shared": True
    }

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def source(self):
        tools.get("{url}/releases/download/{name}-{version}/{name}-{version}.tar.gz".format(url=self.homepage,
                                                                                            name=self.name,
                                                                                            version=self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    _autotools = False

    def _configure_autotools(self):
        if not self._autotools:
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            self._autotools.fpic = True
            with tools.chdir(self._source_subfolder):
                self._autotools.configure()

        return self._autotools

    def build(self):
        autotools = self._configure_autotools()
        with tools.chdir(self._source_subfolder):
            autotools.make()

    def package(self):
        autotools = self._configure_autotools()
        with tools.chdir(self._source_subfolder):
            autotools.install()
        self.copy("*.cmake", src="src", dst="cmake")

    def package_info(self):
        self.cpp_info.name = self.name
        self.cpp_info.builddirs.append('cmake')
