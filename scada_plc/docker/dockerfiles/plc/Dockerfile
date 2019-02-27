FROM centos

MAINTAINER adc - version .002

COPY shared /usr/local/bin/

RUN ["/bin/chmod", "+x", "/usr/local/bin/arduino.py"]

WORKDIR /usr/local/bin/

ENTRYPOINT ["/usr/local/bin/arduino.py"]
