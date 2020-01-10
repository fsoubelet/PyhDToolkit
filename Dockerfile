# NOTA BENE
# YOU SHOULD RUN THIS CONTAINER WITH THE --init OPTION

# STEP 1 - Base image
FROM ubuntu:18.04

# STEP 2 & 3 - Environment variables needed by miniconda install
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

# STEP 4 - Update Ubuntu and install necessary packages
RUN apt-get -qq update --fix-missing > /dev/null && \
    apt-get -qq install -y wget \
    bzip2 \
    ca-certificates \
    curl \
    git \
    build-essential  > /dev/null && \
    apt-get clean > /dev/null && \
    rm -rf /var/lib/apt/lists/*

# STEP 5 - Install miniconda3
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-4.7.12.1-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda >/dev/null && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean --all --quiet --yes && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    /opt/conda/bin/conda update -n base -c defaults conda --yes --quiet > /dev/null && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate PHD" >> ~/.bashrc

# STEP 6 - Get a copy of this package
# RUN git clone https://github.com/fsoubelet/PyhDToolkit /pyhdtoolkit
COPY . /pyhdtoolkit

# STEP 7 - Create the PHD conda environment
RUN conda env create --file /pyhdtoolkit/docker_conda_env.yml --force  > /dev/null && \
    /opt/conda/bin/conda clean --all --quiet --yes > /dev/null

# STEP 8 - Start a bash shell at runtime
CMD [ "/bin/bash" ]