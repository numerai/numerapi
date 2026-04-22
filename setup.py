from setuptools import find_packages, setup


def load(path):
    return open(path, "r").read()


numerapi_version = "2.23.0"


classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Topic :: Scientific/Engineering",
]


if __name__ == "__main__":
    setup(
        name="numerapi",
        version=numerapi_version,
        maintainer="uuazed",
        maintainer_email="uuazed@gmail.com",
        description="Automatically download and upload data for the Numerai machine learning competition",
        long_description=load("README.md"),
        long_description_content_type="text/markdown",
        url="https://github.com/uuazed/numerapi",
        platforms="OS Independent",
        classifiers=classifiers,
        license="MIT License",
        package_data={"numerapi": ["LICENSE", "README.md", "py.typed"]},
        packages=find_packages(exclude=["tests"]),
        install_requires=[
            "requests",
            "pytz",
            "python-dateutil",
            "tqdm>=4.29.1",
            "click>=7.0",
            "pandas>=1.1.0",
        ],
        entry_points={"console_scripts": ["numerapi = numerapi.cli:cli"]},
    )
