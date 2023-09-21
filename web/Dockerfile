FROM python:3.8.18-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_VERSION='23.2.1'
ENV SETUPTOOLS_VERSION='68.1.2'
ENV PIP_TOOLS_VERSION='7.3.0'
# As per Centos installation
ENV VE_VERSION='20.13.0'

WORKDIR /srv
COPY requirements/requirements.txt /srv/temmpo/src/temmpo/

# Update system packages and install dependencies
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
    rm -rf /var/lib/apt/lists/*  && \ 
    pip install --no-cache-dir -U pip==$PIP_VERSION && \ 
    pip install --no-cache-dir -U setuptools==$SETUPTOOLS_VERSION && \ 
    pip install --no-cache-dir pip-tools==$PIP_TOOLS_VERSION && \ 
    pip install --no-cache-dir virtualenv==$VE_VERSION && \ 
    virtualenv temmpo && \ 
    /srv/temmpo/bin/pip install --upgrade pip==$PIP_VERSION  && \ 
    /srv/temmpo/bin/pip install --no-cache-dir --no-deps -r /srv/temmpo/src/temmpo/requirements.txt  && \ 
    apt-get -y remove gcc && \
    apt-get -y autoremove && \
    apt-get clean

COPY . /srv/temmpo/src/temmpo/
VOLUME [ "/srv/temmpo/src/temmpo/" ]
