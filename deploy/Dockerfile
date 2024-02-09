FROM python:3.8.18-slim

ARG REQUIREMENTS_FILE='requirements.txt'

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_VERSION='24.0'
ENV SETUPTOOLS_VERSION='69.0.3'
ENV PIP_TOOLS_VERSION='7.3.0'
# As per CentOS installation
ENV VE_VERSION='20.24.5'

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
            # ref: https://github.com/mixkorshun/django-safe-filefield requires libmagic
            libmagic1 \
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

COPY requirements/$REQUIREMENTS_FILE /srv
RUN pip install --no-deps -r /srv/$REQUIREMENTS_FILE

CMD [ "pip", "check" ]