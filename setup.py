#!/usr/bin/env python

# Standard library modules.
from pathlib import Path

# Third party modules.
from setuptools import setup, find_packages

# Local modules.
import versioneer

# Globals and constants variables.
BASEDIR = Path(__file__).parent.resolve()

with open(BASEDIR.joinpath("README.md"), "r") as fp:
    LONG_DESCRIPTION = fp.read()

PACKAGES = find_packages(exclude=["project", "tests", "tests.*"])

PACKAGE_DATA = {
    "django_cd": [
        "templates/*.html",
        "templates/django_cd/*.html",
        "static/*.svg",
        "static/*.ico",
        "static/*.css",
    ],
}

with open(BASEDIR.joinpath("requirements.txt"), "r") as fp:
    INSTALL_REQUIRES = fp.read().splitlines()

EXTRAS_REQUIRE = {}
with open(BASEDIR.joinpath("requirements-dev.txt"), "r") as fp:
    EXTRAS_REQUIRE["dev"] = fp.read().splitlines()
with open(BASEDIR.joinpath("requirements-test.txt"), "r") as fp:
    EXTRAS_REQUIRE["test"] = fp.read().splitlines()

CMDCLASS = versioneer.get_cmdclass()

ENTRY_POINTS = {}

setup(
    name="django-cd",
    version=versioneer.get_version(),
    url="https://github.com/ppinard/django-cd",
    author="Philippe Pinard",
    author_email="philippe.pinard@gmail.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    description="Continuous deloyment",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license="MIT license",
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    cmdclass=CMDCLASS,
    entry_points=ENTRY_POINTS,
)
