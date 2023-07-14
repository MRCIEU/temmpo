FROM python:3.8.17-slim

ENV PIP_VERSION='23.1.2'
ENV SETUPTOOLS_VERSION='68.0.0'
ENV PIP_TOOLS_VERSION='6.14.0'
ENV VE_VERSION='20.13.0'

# Update system packages and install dependnecies, e.g Postgresl and Pillow support"
RUN apt update -y && \
    apt-get install -y --no-install-recommends \
            bzip2 \
            build-essential \
            clamav \
            clamav-data \
            clamav-daemon \
            # clamav-devel \
            curl \
            default-mysql-client \
            default-libmysqlclient-dev \
            gcc \
            g++ \
            libffi-dev  \
            libpq-dev \
            libssl-dev \
            pkg-config \
            python3-dev \
            python3-lxml \
            python3-setuptools \
            python3-wheel \
            wait-for-it \
            zlib1g-dev &&  \ 
    apt-get clean && \
    apt-get -y autoremove && \ 
    rm -rf /var/lib/apt/lists/*

RUN pip install -U pip==$PIP_VERSION
RUN pip install -U setuptools==$SETUPTOOLS_VERSION
RUN pip install pip-tools==$PIP_TOOLS_VERSION
RUN pip install virtualenv==$VE_VERSION

WORKDIR /srv

VOLUME [ "/srv" ]