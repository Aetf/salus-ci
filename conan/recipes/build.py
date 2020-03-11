#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build, Test and Deploy Conan packages"""
from pathlib import Path
from collections import defaultdict
from cpt.packager import ConanMultiPackager
import yaml
import logging


class ConanPackager(object):
    def __init__(self):
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)

    def run(self):
        for recipe in Path('.').iterdir():
            if not recipe.is_dir():
                continue
            self.build_single_recipe(recipe)

    def _detect_versions(self, recipe):
        versionyml = recipe / 'config.yml'
        if versionyml.exists():
            versions_by_folder = defaultdict(list)
            with versionyml.open() as f:
                for version, cfg in yaml.safe_load(f)['versions'].items():
                    folder = cfg['folder']
                    versions_by_folder[folder].append(version)
        else:
            versions_by_folder = {d.name: [d.name] for d in recipe.iterdir()}
        return versions_by_folder

    def build_single_recipe(self, recipe):
        versions_by_folder = self._detect_versions(recipe)
        for folder, versions in versions_by_folder.items():
            conanfile = str(recipe / folder / 'conanfile.py')
            builder = ConanMultiPackager(conanfile=conanfile)
            for version in versions:
                reference = '{}/{}'.format(recipe.name, version)
                logging.info('Building {}'.format(reference))
                builder.add_common_builds(reference=reference, pure_c=False)
            # we only want libstdc++11 ABI
            builder.remove_build_if(lambda build: '11' not in build.settings["compiler.libcxx"])
            builder.run()


if __name__ == "__main__":
    cp = ConanPackager()
    cp.run()
