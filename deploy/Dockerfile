FROM python:3.8.19-slim

ARG REQUIREMENTS_FILE='requirements.txt'

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_VERSION='24.1.1'
ENV SETUPTOOLS_VERSION='70.2.0'
ENV PIP_TOOLS_VERSION='7.4.1'
# NB: Version 15.1.0 is installed on RHEL
ENV VE_VERSION='20.26.3' 

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
            firefox-esr \
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
            # xvfb xauth
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

COPY requirements/$REQUIREMENTS_FILE /srv
RUN pip install --no-deps -r /srv/$REQUIREMENTS_FILE

CMD [ "pip", "check" ]