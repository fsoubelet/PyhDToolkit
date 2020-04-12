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
    "numpy",
    "scipy",
    "matplotlib>3.0",
    "fsbox>=0.2.0",
    "pandas<1.0",
    "tfs-pandas>=1.0.3",
]

# Extra dependencies
EXTRA_DEPENDENCIES = {
    "setup": ["pytest-runner"],
    "test": ["pytest>=5.2", "pytest-cov>=2.7", "hypothesis>=5.0.0", "attrs>=19.2.0"],
    "madx": ["cpymad>=1.4"],
    "tqdm": ["tqdm>4.0"],
}
EXTRA_DEPENDENCIES.update({"all": [elem for list_ in EXTRA_DEPENDENCIES.values() for elem in list_]})


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
    tests_require=EXTRA_DEPENDENCIES["test"],
    setup_requires=EXTRA_DEPENDENCIES["setup"],
    extras_require=EXTRA_DEPENDENCIES,
)
