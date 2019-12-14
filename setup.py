from pathlib import Path

import setuptools

TOPLEVEL_DIRECTORY = Path(__file__).parent.absolute()
ABOUT = TOPLEVEL_DIRECTORY / "pyhdtoolkit" / "__version__.py"
README = TOPLEVEL_DIRECTORY / "README.md"

about: dict = {}
with ABOUT.open("r") as f:
    exec(f.read(), about)

with README.open("r") as docs:
    long_description = docs.read()

# Not really "requires" but I just use them all the time, might as well come with.
install_requires = ["matplotlib>=3.1.1"]

tests_require = [
    # Pytest needs to come last: https://bitbucket.org/pypa/setuptools/issue/196/
    "pytest"
]

setuptools.setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=about["__author__"],
    author_email=about["__author_email__"],
    url=about["__url__"],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=install_requires,
    license=about["__license__"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Utilities",
    ],
    tests_require=tests_require,
)
