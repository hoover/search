FROM python:3
ENV PYTHONUNBUFFERED 1

RUN echo 'deb http://deb.debian.org/debian jessie non-free' >> /etc/apt/sources.list
RUN echo 'deb http://deb.debian.org/debian jessie-updates non-free' >> /etc/apt/sources.list
RUN echo 'deb http://security.debian.org jessie/updates non-free' >> /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y --no-install-recommends qrencode
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/hoover/search
WORKDIR /opt/hoover/search

ADD requirements.txt /opt/hoover/search/
RUN pip install -r requirements.txt

ADD . /opt/hoover/search/