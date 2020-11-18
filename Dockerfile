# ------------------------------------------------------------------------------
# Dockerfile to build basic Oracle Linux container images
# Based on Oracle Linux 7
# ------------------------------------------------------------------------------

# Set the base image to Oracle Linux 7
FROM oraclelinux:7

# File Author / Maintainer
# Use LABEL rather than deprecated MAINTAINER
# MAINTAINER Isaias Ramirez (soote1.ir@gmail.com)

WORKDIR /home/oscaptool

LABEL maintainer="soote1.ir@gmail.com"

# install required dependencies
RUN yum -y install scap-security-guide
RUN yum -y install python3
RUN pip3 install pipenv

ADD . ./oscaptool/

WORKDIR /home/oscaptool/oscaptool

RUN pipenv --python /bin/python3.6 install -e .
# End