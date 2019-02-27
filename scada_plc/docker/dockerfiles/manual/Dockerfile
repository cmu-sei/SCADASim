FROM localhost:5000/raindrop_base

MAINTAINER adc - version .001

COPY shared /usr/local/bin/

RUN ["/bin/chmod","+x","/usr/local/bin/poc_browse.py"]

WORKDIR /usr/local/bin/

#ENTRYPOINT ["/usr/local/bin/poc_browse.py"]


