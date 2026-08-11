from setuptools import find_packages, setup


def load(path):
    return open(path, "r").read()


numerapi_version = "3.1.0.dev0"

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Scientific/Engineering",
]


if __name__ == "__main__":
    setup(
        name="numerapi",
        version=numerapi_version,
        maintainer="Numerai",
        maintainer_email="tournament@numer.ai",
        description="Automatically download and upload data for the Numerai machine learning competition",
        long_description=load("README.md"),
        long_description_content_type="text/markdown",
        url="https://github.com/numerai/numerapi",
        platforms="OS Independent",
        classifiers=classifiers,
        python_requires=">=3.10",
        license="MIT License",
        package_data={"numerapi": ["LICENSE", "README.md", "py.typed"]},
        packages=find_packages(exclude=["tests"]),
        install_requires=[
            "requests",
            "pytz",
            "python-dateutil",
            "tqdm>=4.29.1",
            "click>=7.0",
            "fsspec[http]",
            "pandas>=1.1.0; python_version < '3.14'",
            "pandas>=2.3.3; python_version >= '3.14'",
        ],
        entry_points={"console_scripts": ["numerapi = numerapi.cli:cli"]},
    )
