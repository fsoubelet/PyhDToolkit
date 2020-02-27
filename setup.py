import pathlib

import setuptools

# The directory containing this file
TOPLEVEL_DIR = pathlib.Path(__file__).parent.absolute()
ABOUT_FILE = TOPLEVEL_DIR / "pyhdtoolkit" / "__init__.py"
README = TOPLEVEL_DIR / "README.md"

# Information on the package
ABOUT_PACKAGE: dict = {}
with ABOUT_FILE.open("r") as f:
    exec(f.read(), ABOUT_PACKAGE)

with README.open("r") as docs:
    long_description = docs.read()

# Dependencies for the package itself
DEPENDENCIES = [
    "fsbox>=0.1.0",
    "numpy>=1.14.1",
    "pandas>=0.24.0,<1.0",
    "scipy>=1.0.0",
    "scikit-learn>=0.20.3",
    "tfs-pandas>=1.0.3",
    "generic-parser>=1.0.6",
    "sdds>=0.1.3",
    "pytz>=2018.9",
    "tqdm>=4.41",
]


# Dependencies that should only be installed for test purposes
TEST_DEPENDENCIES = ["pytest>=5.2", "pytest-cov>=2.6", "h5py>=2.7.0", "hypothesis>=3.23.0", "attrs>=19.2.0"]

# pytest-runner to be able to run pytest via setuptools
SETUP_REQUIRES = ["pytest-runner"]


setuptools.setup(
    name=ABOUT_PACKAGE["__title__"],
    version=ABOUT_PACKAGE["__version__"],
    description=ABOUT_PACKAGE["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=ABOUT_PACKAGE["__author__"],
    author_email=ABOUT_PACKAGE["__author_email__"],
    url=ABOUT_PACKAGE["__url__"],
    packages=setuptools.find_packages(exclude=["tests", "doc", "bin"]),
    python_requires=">=3.6",
    license=ABOUT_PACKAGE["__license__"],
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
    install_requires=DEPENDENCIES,
    tests_require=DEPENDENCIES + TEST_DEPENDENCIES,
    setup_requires=SETUP_REQUIRES,
)
