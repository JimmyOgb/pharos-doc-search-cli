from setuptools import setup, find_packages

setup(
    name="pharos-doc-search-cli",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pharos-docs=pharos_docs.cli:main",
        ],
    },
)
