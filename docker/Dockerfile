# Starts automatically with --tiny and with a 'work' folder to mount things into
# Example for jupyterlab, mounting a local directory:
# docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v <host_dir_to_mount>:/home/jovyan/work <container_name>

# STEP 1 - Base image
FROM jupyter/base-notebook

# STEP 2 - Label
LABEL maintainer="Felix Soubelet <felix.soubelet@cern.ch>"

# STEP 3 - Let mamba install packages
RUN mamba install --yes \
    black \
    click \
    fastparquet \
    h5py \
    hdf5 \
    ipykernel \
    isort \
    joblib \
    loguru \
    matplotlib \
    numpy \
    pandas \
    pendulum \
    pyarrow \
    pydantic \
    requests \
    rich \
    scikit-learn \
    sdds \
    sympy \
    tfs-pandas \
    scipy && \
    python -m pip install pyhdtoolkit pynaff && \
    conda clean --all --quiet --yes \