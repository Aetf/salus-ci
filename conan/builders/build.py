#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build, Test and Deploy Docker images for Conan project"""
import collections
import os
import logging
import subprocess
import requests
import time
from humanfriendly import format_size
from conans import __version__ as client_version
from conans import tools
from cpt.ci_manager import CIManager
from cpt.printer import Printer


class ConanDockerTools(object):
    """Execute all build process for Docker image
    """

    def __init__(self):
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)

        self.variables = self._get_variables()

        filter_gcc_compiler_version = self.variables.gcc_versions
        filter_clang_compiler_version = self.variables.clang_versions
        filter_visual_compiler_version = self.variables.visual_versions

        Compiler = collections.namedtuple("Compiler", "name, versions, pretty")
        self.gcc_compiler = Compiler(name="gcc", versions=filter_gcc_compiler_version, pretty="gcc")
        self.clang_compiler = Compiler(name="clang", versions=filter_clang_compiler_version, pretty="clang")
        self.visual_compiler = Compiler(name="msvc", versions=filter_visual_compiler_version, pretty="Visual Studio")
        self.loggedin = False
        self.service = None

        logging.info("""
    The follow compiler versions will be built:
        GCC: %s
        CLANG: %s
        VISUAL STUDIO: %s
        """ % (self.gcc_compiler.versions, self.clang_compiler.versions, self.visual_compiler.versions))

    def _get_variables(self):
        """Load environment variables to configure
        :return: Variables
        """
        docker_upload = self._get_boolean_var("DOCKER_UPLOAD")
        docker_upload_retry = os.getenv("DOCKER_UPLOAD_RETRY", 10)
        docker_upload_only_when_stable = self._get_boolean_var("DOCKER_UPLOAD_ONLY_WHEN_STABLE", "true")
        build_server = self._get_boolean_var("BUILD_CONAN_SERVER_IMAGE")
        build_tests = self._get_boolean_var("BUILD_CONAN_TESTS")
        build_test_azure = self._get_boolean_var("BUILD_CONAN_TEST_AZURE")
        docker_password = os.getenv("DOCKER_PASSWORD", "").replace('"', '\\"')
        docker_username = os.getenv("DOCKER_USERNAME", "salus/salus/builder")
        docker_login_username = os.getenv("DOCKER_LOGIN_USERNAME", "Aetf")
        docker_registry = os.getenv("DOCKER_REGISTRY", "registry.gitlab.com")
        docker_build_tag = os.getenv("DOCKER_BUILD_TAG", "latest")
        docker_archs = os.getenv("DOCKER_ARCHS").split(",") if os.getenv("DOCKER_ARCHS") else [
            "x86_64"
        ]
        docker_cross = os.getenv("DOCKER_CROSS", False)
        docker_cache = self._get_boolean_var("DOCKER_CACHE", "true")
        docker_distro = os.getenv("DOCKER_DISTRO").split(",") if os.getenv("DOCKER_DISTRO") else []
        conan_version = os.getenv("CONAN_VERSION", client_version)
        os.environ["CONAN_VERSION"] = conan_version
        os.environ["DOCKER_USERNAME"] = docker_username
        os.environ["DOCKER_BUILD_TAG"] = docker_build_tag
        gcc_versions = os.getenv("GCC_VERSIONS").split(",") if os.getenv("GCC_VERSIONS") else []
        clang_versions = os.getenv("CLANG_VERSIONS").split(",") if os.getenv("CLANG_VERSIONS") else []
        visual_versions = os.getenv("VISUAL_VERSIONS").split(",") if os.getenv("VISUAL_VERSIONS") else []
        sudo_command = os.getenv("SUDO_COMMAND", "")
        if tools.os_info.is_linux and not sudo_command:
            sudo_command = "sudo" if os.geteuid() != 0 else sudo_command
        Variables = collections.namedtuple(
            "Variables", "docker_upload, docker_password, "
            "docker_username, docker_login_username, docker_registry, "
            "gcc_versions, docker_distro, "
            "clang_versions, visual_versions, build_server, "
            "docker_build_tag, docker_archs, sudo_command, "
            "docker_upload_only_when_stable, docker_cross, docker_cache, "
            "build_tests, build_test_azure docker_upload_retry")
        return Variables(docker_upload, docker_password,
                         docker_username, docker_login_username, docker_registry,
                         gcc_versions, docker_distro, clang_versions, visual_versions, build_server,
                         docker_build_tag, docker_archs, sudo_command, docker_upload_only_when_stable,
                         docker_cross, docker_cache, build_tests, build_test_azure, docker_upload_retry)

    def _get_boolean_var(self, var, default="false"):
        """ Parse environment variable as boolean type
        :param var: Environment variable name
        """
        return os.getenv(var, default.lower()).lower() in ["1", "true", "yes"]

    def login(self):
        """ Perform login on Docker server (hub.docker)
        """
        if tools.os_info.is_windows:
            logging.warn("Skipped login, Windows is not supported.")
            return

        if self.variables.docker_upload_only_when_stable:
            printer = Printer()
            ci_manager = CIManager(printer)
            if ci_manager.get_branch() != "master" or ci_manager.is_pull_request():
                logging.info("Skipped login, is not stable branch")
                return

        if not self.variables.docker_upload:
            logging.info("Skipped login, DOCKER_UPLOAD is not activated")
            return

        if not self.variables.docker_password:
            logging.warning("Skipped login, DOCKER_PASSWORD is missing!")
            return

        if not self.variables.docker_login_username:
            logging.warning("Skipped login, DOCKER_LOGIN_USERNAME is missing!")
            return

        logging.info("Login to Docker registry account")
        result = subprocess.call([
            "docker", "login", "-u", self.variables.docker_login_username, "-p",
            self.variables.docker_password,
            self.variables.docker_registry
        ])
        if result != os.EX_OK:
            raise RuntimeError("Could not login username %s "
                               "to Docker hub." % self.variables.docker_login_username)

        logging.info("Logged in Docker registry account with success")
        self.loggedin = True

    @property
    def created_image_name(self):
        """ Retrieve Docker image name
        """
        assert self.service is not None
        name = '/'.join([self.variables.docker_registry, self.variables.docker_username, self.service])
        return "%s:%s" % (name, self.variables.docker_build_tag)

    @property
    def tagged_image_name(self):
        assert self.service is not None
        name = '/'.join([self.variables.docker_registry, self.variables.docker_username, self.service])
        return "%s:%s" % (name, client_version)

    def build(self):
        """Call docker build to create a image
        :param service: service in compose e.g gcc54
        :param context: image dir
        """
        logging.info("Starting build for service %s." % self.service)
        if self.variables.docker_cache:
            logging.info("Starting pull for service %s." % self.service)
            subprocess.check_call("docker-compose pull %s" % self.service, shell=True)
        no_cache = "" if self.variables.docker_cache else "--no-cache"
        subprocess.check_call("docker-compose build %s %s" % (no_cache, self.service), shell=True)

        output = subprocess.check_output(
            "docker image inspect %s --format '{{.Size}}'" % self.created_image_name,
            shell=True
        )
        size = int(output.decode().strip())
        logging.info("%s image size: %s" % (self.created_image_name, format_size(size)))

    def linter(self, build_dir):
        """Execute hadolint to check possible prone errors

        :param build_dir: Directory with Dockerfile
        """
        if tools.os_info.is_windows:
            logging.warn("Skipping linter, Windows is not supported.")
            return

        logging.info("Executing hadolint on directory %s." % build_dir)
        subprocess.call(
            'docker run --rm -i hadolint/hadolint < %s/Dockerfile' % build_dir, shell=True)

    def test(self, arch, compiler_name, compiler_version, distro=""):
        """Validate Docker image by Conan install
        :param arch: Name of he architecture
        :param compiler_name: Compiler to be specified as conan setting e.g. clang
        :param compiler_version: Compiler version to be specified as conan setting e.g. 3.8
        :param service: Docker compose service name
        :param distro: Use other linux distro
        """
        logging.info("Testing Docker by service %s." % self.service)
        try:
            if compiler_name == "Visual Studio":
                self.test_visual_studio(arch, compiler_name, compiler_version)
            else:
                self.test_linux(arch, compiler_name, compiler_version, distro)
        finally:
            subprocess.call("docker stop %s" % self.service, shell=True)
            subprocess.call("docker rm %s" % self.service, shell=True)

    def test_visual_studio(self, arch, compiler_name, compiler_version):
        """ Validate Windows Docker image by Conan install
        :param arch: Name of he architecture
        :param compiler_name: Compiler to be specified as conan setting e.g. clang
        :param compiler_version: Compiler version to be specified as conan setting e.g. 3.8
        """
        subprocess.check_call("docker exec %s %s pip -q install -U conan" % (self.service, self.variables.sudo_command), shell=True)
        subprocess.check_call("docker exec %s %s pip -q install -U conan_package_tools" % (self.service, self.variables.sudo_command), shell=True)
        subprocess.check_call("docker exec %s conan user" % self.service, shell=True)

        subprocess.check_call('docker exec %s conan install lz4/1.8.3@bincrafters/stable -s '
                            'arch=%s -s compiler="%s" -s compiler.version=%s '
                            '-s compiler.runtime=MD --build' %
                            (self.service, arch, compiler_name,
                            compiler_version), shell=True)

        subprocess.check_call('docker exec %s conan install gtest/1.8.1@bincrafters/stable -s '
                            'arch=%s -s compiler="%s" -s compiler.version=%s '
                            '-s compiler.runtime=MD --build' %
                            (self.service, arch, compiler_name,
                            compiler_version), shell=True)

    def test_linux(self, arch, compiler_name, compiler_version, distro):
        """ Validate Linux Docker image by Conan install
        :param arch: Name of he architecture
        :param compiler_name: Compiler to be specified as conan setting e.g. clang
        :param compiler_version: Compiler version to be specified as conan setting e.g. 3.8
        :param service: Docker compose service name
        :param distro: Use other linux distro
        """
        libcxx_list = ["libstdc++"] if compiler_name == "gcc" else ["libstdc++", "libc++"]
        if self.variables.docker_cross == "android":
            libcxx_list = ["libc++"]
        sudo_commands = ["", "sudo"] if distro else ["", "sudo", "sudo -E"]
        subprocess.check_call("docker run -t -d --name %s %s" % (self.service, self.created_image_name), shell=True)

        for sudo_command in sudo_commands:

            logging.info("Testing command prefix: '{}'".format(sudo_command))
            output = subprocess.check_output(
                "docker exec %s %s python3 --version" % (self.service, sudo_command), shell=True)
            assert "Python 3" in output.decode()
            logging.info("Found %s" % output.decode().rstrip())

            output = subprocess.check_output(
                "docker exec %s %s pip --version" % (self.service, sudo_command), shell=True)
            assert "python 3" in output.decode()
            logging.info("Found pip (Python 3)")

            output = subprocess.check_output(
                "docker exec %s %s pip3 --version" % (self.service, sudo_command), shell=True)
            assert "python 3" in output.decode()
            logging.info("Found pip3 (Python 3)")

            output = subprocess.check_output(
                "docker exec %s %s pip show conan" % (self.service, sudo_command), shell=True)
            assert "python3" in output.decode()
            logging.info("Found Conan (Python 3)")

            output = subprocess.check_output(
                "docker exec %s %s python --version" % (self.service, sudo_command), shell=True)
            assert "Python 3" in output.decode()
            logging.info("Default Python version: %s" % output.decode().rstrip())

            subprocess.check_call(
                "docker exec %s %s pip install --no-cache-dir -U conan_package_tools" %
                (self.service, sudo_command),
                shell=True)
            subprocess.check_call(
                "docker exec %s %s pip install --no-cache-dir -U conan" % (self.service, sudo_command),
                shell=True)
            subprocess.check_call("docker exec %s conan user" % self.service, shell=True)

            if compiler_name == "clang" and compiler_version == "7":
                compiler_version = "7.0"  # FIXME: Remove this when fixed in conan

        subprocess.check_call(
            "docker exec %s conan install lz4/1.8.3@bincrafters/stable -s "
            "arch=%s -s compiler=%s -s compiler.version=%s --build" %
            (self.service, arch, compiler_name, compiler_version),
            shell=True)

        for libcxx in libcxx_list:
            subprocess.check_call(
                "docker exec %s conan install gtest/1.8.1@bincrafters/stable -s "
                "arch=%s -s compiler=%s -s compiler.version=%s "
                "-s compiler.libcxx=%s --build" % (self.service, arch, compiler_name,
                                                   compiler_version, libcxx),
                shell=True)

    def deploy(self):
        """Upload Docker image to dockerhub
        """
        if not self.loggedin:
            logging.info("Skipping upload. Docker account is not connected.")
            return

        for retry in range(int(self.variables.docker_upload_retry)):
            try:
                logging.info("Upload Docker image from service %s to Docker hub." % self.service)
                subprocess.check_call("docker-compose push %s" % self.service, shell=True)
                logging.info("Upload Docker image %s" % self.tagged_image_name)
                subprocess.check_call("docker push %s" % self.tagged_image_name, shell=True)

                if self.service == "clang7":
                    logging.info("Clang 7 will upload the alias Clang 7.0")
                    subprocess.check_call("docker push %s" % self.tagged_image_name.replace("clang7", "clang70"),
                                          shell=True)
                    subprocess.check_call("docker push %s" % self.created_image_name.replace("clang7", "clang70"),
                                          shell=True)
                break
            except:  # noqa: E377
                if retry == int(self.variables.docker_upload_retry):
                    raise RuntimeError("Could not upload Docker image {}".format(self.tagged_image_name))
                logging.warn("Could not upload Docker image. Retry({})".format(retry+1))
                time.sleep(3)

    def tag(self):
        """Apply Docker tag name
        """
        logging.info("Creating Docker tag %s" % self.tagged_image_name)
        subprocess.check_call("docker tag %s %s" % (self.created_image_name, self.tagged_image_name), shell=True)

        # clang7 is represented by clang7.0 in Conan settings
        if self.service == "clang7":
            logging.info("Clang 7 will produce the alias Clang 7.0")
            subprocess.check_call(
                "docker tag %s %s" % (self.created_image_name, self.tagged_image_name.replace("clang7", "clang70")),
                shell=True
            )
            subprocess.check_call(
                "docker tag %s/clang7 %s/clang70" % (self.variables.docker_username, self.variables.docker_username),
                shell=True
            )

    def info(self):
        """Show Docker image info
        """
        logging.info("Show Docker image %s size:" % self.created_image_name)
        subprocess.call('docker images %s' % self.created_image_name, shell=True)
        logging.info("Show Docker image %s info:" % self.created_image_name)
        subprocess.call('docker inspect %s' % self.created_image_name, shell=True)

    def process_regular_images(self):
        cross = "" if not self.variables.docker_cross else "%s-" % self.variables.docker_cross
        for arch in self.variables.docker_archs:
            for compiler in [self.gcc_compiler, self.clang_compiler, self.visual_compiler]:
                for version in compiler.versions:
                    tag_arch = "" if arch == "x86_64" else "-%s" % arch
                    service = "%s%s%s%s" % (cross, compiler.name, version.replace(".", ""), tag_arch)
                    build_dir = "%s%s_%s%s" % (cross, compiler.name, version, tag_arch)

                    self.service = service
                    self.login()
                    self.linter(build_dir)
                    self.build()
                    self.tag()
                    self.test(arch, compiler.name, version)
                    self.info()
                    self.deploy()

    def run(self):
        """Execute all 3 stages for all versions in compilers list
        """
        self.process_regular_images()


if __name__ == "__main__":
    conan_docker_tools = ConanDockerTools()
    conan_docker_tools.run()
