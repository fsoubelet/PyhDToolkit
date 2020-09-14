# Starts automatically with --tiny and with a 'work' folder to mount things into
# Example for jupyterlab, mounting a local directory:
# docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v <host_dir_to_mount>:/home/jovyan/work <container_name>

# STEP 1 - Base image
FROM jupyter/base-notebook

# STEP 2 & 3 - Label and environment file
LABEL maintainer="Felix Soubelet <felix.soubelet@cern.ch>"
COPY environment.yml /home/jovyan/environment.yml

# STEP 4 - Create the PHD conda environment
RUN conda env create --file ./environment.yml --force  > /dev/null \
    && /opt/conda/bin/conda clean --all --quiet --yes > /dev/null \
    && /opt/conda/envs/PHD/bin/ipython kernel install --user --name=PHD