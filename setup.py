import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

name = "nerdo"

setuptools.setup(
    name=name,
    version="0.0.1",
    author="Iago Salgado",
    author_email="igsalgado@protonmail.com",
    description="NEwly Registered DOmains",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    url="https://github.com/hacklego/nerdo",
    entry_points={
        "console_scripts": [
            "nerdo = nerdo.main:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
