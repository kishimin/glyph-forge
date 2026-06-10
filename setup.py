from setuptools import setup, find_packages

setup(
    name="glyph_forge",
    version="1.0.0",
    description="generate character art by many character",
    author="kishimin",
    author_email="r8a1wu2@gmail.com",
    url="https://github.com/kishimin/glyph-forge",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
