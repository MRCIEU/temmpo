FROM python:3.8.18-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_VERSION='23.2.1'
ENV SETUPTOOLS_VERSION='68.1.2'
ENV PIP_TOOLS_VERSION='7.3.0'
# As per Centos installation
ENV VE_VERSION='20.13.0'

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
    rm -rf /var/lib/apt/lists/*

RUN pip install -U pip==$PIP_VERSION
RUN pip install -U setuptools==$SETUPTOOLS_VERSION
RUN pip install pip-tools==$PIP_TOOLS_VERSION
RUN pip install virtualenv==$VE_VERSION

WORKDIR /srv

VOLUME [ "/srv" ]

# TODO: Replace temp basic build test as image is developed further
COPY requirements/requirements.txt /srv
RUN pip install --no-deps -r /srv/requirements.txt
CMD [ "pip", "check" ]