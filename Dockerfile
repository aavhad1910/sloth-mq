# Download base image ubuntu 20.04
FROM ubuntu:20.04
LABEL maintainer="Atul, Paritosh, Raj, Mrunal"
RUN apt-get update
RUN apt-get update && apt-get install -y apt-transport-https
RUN apt-get -y install python3-pip
WORKDIR /code
ADD . /code
RUN pip3 install -r requirements.txt
