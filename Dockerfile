FROM python:3-slim-stretch
RUN apt-get update
RUN apt-get -y install procps wget unzip build-essential libcurl4-openssl-dev libssl-dev
RUN wget -O r53-dyndns-master.zip 'https://github.com/ozkolonur/r53-dyndns/archive/master.zip'
RUN unzip r53-dyndns-master.zip
RUN rm r53-dyndns-master.zip
RUN pip install -r /r53-dyndns-master/requirements.txt
RUN cd /r53-dyndns-master && python setup.py install
RUN mkdir -p /var/log/r53-dyndns/
CMD r53-dyndns.py -d -c /etc/r53-dyndns.cfg
