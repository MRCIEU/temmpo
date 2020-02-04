from centos:7.7.1908

ENV PYTHONDONTWRITEBYTECODE=1

# Utilities
RUN yum -y install wget
RUN yum -y install epel-release
RUN yum -y update
RUN yum -y install python-devel
RUN yum -y install python-wheel
RUN yum -y install python-magic
RUN yum -y install python-pip
RUN yum -y install python-virtualenv
RUN yum -y install libxml2-python
RUN yum -y install libxml2-devel
RUN yum -y install libxslt-python
RUN yum -y install libxslt-devel
RUN yum -y install python-lxml
RUN yum -y install gcc gcc-c++
RUN yum -y install wget
RUN yum -y install mariadb
RUN yum -y install mariadb-devel
RUN yum -y install mysql-devel
RUN yum -y install mysql-connector-python
RUN yum -y install mysql-utilities
RUN wget https://dev.mysql.com/get/mysql57-community-release-el7-11.noarch.rpm
RUN yum -y localinstall mysql57-community-release-el7-11.noarch.rpm
RUN yum -y install mysql-community-libs
RUN yum -y install mysql-community-client
RUN yum list installed
RUN pip install virtualenv
RUN pip install fabric==1.13.1

# Create virtual environment
RUN mkdir -p /usr/local/projects/temmpo/lib/
WORKDIR /usr/local/projects/temmpo/lib/
RUN virtualenv dev
WORKDIR /usr/local/projects/temmpo/lib/dev/
RUN ./bin/pip install -U pip==19.1.1
RUN ./bin/pip install -U pip-tools==4.3.0
RUN ./bin/pip install -U setuptools==41.0.1
RUN ./bin/pip freeze

# Copy just requirements into container
COPY requirements/dev.txt src/temmpo/requirements/dev.txt
RUN ./bin/pip install -r src/temmpo/requirements/dev.txt
RUN ./bin/pip-sync src/temmpo/requirements/dev.txt

# Create expected directory structure
RUN mkdir -p /usr/local/projects/temmpo/var/results/testing/v1
RUN mkdir -p /usr/local/projects/temmpo/var/results/testing/v3
RUN mkdir -p /usr/local/projects/temmpo/var/abstracts
RUN mkdir -p /usr/local/projects/temmpo/var/data
RUN mkdir -p /usr/local/projects/temmpo/var/log
RUN mkdir -p /usr/local/projects/temmpo/lib/dev/src/temmpo

# Copy application code into container
COPY . src/temmpo/
# TODO DEBUG BUGFIX: Create the expected private settings file for the development host
WORKDIR /usr/local/projects/temmpo/lib/dev/src/temmpo/temmpo/settings

# Set container entry directory to alongside manage.py
WORKDIR /usr/local/projects/temmpo/lib/dev/src/temmpo
