import os
from conans import ConanFile, AutoToolsBuildEnvironment, tools


class GperftoolsConan(ConanFile):
    name = "gperftools"
    license = "BSD-3-Clause"
    url = "https://github.com/Aetf/salus-ci"
    homepage = "https://github.com/gperftools/gperftools"
    description = ("The fastest malloc we’ve seen; works particularly well with threads and STL."
                   "Also: thread-friendly heap-checker, heap-profiler, and cpu-profiler.")
    settings = "os", "compiler", "build_type", "arch"
    short_paths = True

    exports_sources = 'src/*'

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    _autotools = False

    def _configure_autotools(self):
        if not self._autotools:
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            args = ['--disable-static', '--enable-shared']
            with tools.chdir(self._source_subfolder):
                self._autotools.configure(args=args)

        return self._autotools

    def build(self):
        autotools = self._configure_autotools()
        with tools.chdir(self._source_subfolder):
            autotools.make()

    def package(self):
        autotools = self._configure_autotools()
        with tools.chdir(self._source_subfolder):
            autotools.install()
        self.copy("*.cmake", src="src")
        with tools.chdir(os.path.join(self.package_folder, "lib")):
            self.run("rm -f *.la")

    def package_info(self):
        self.cpp_info.name = self.name
