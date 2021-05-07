FROM alpine:3.12.3

RUN set -ex \
      && apk add py3-requests py3-prometheus-client

COPY src/tankutility_exporter.py /root/tankutility_exporter.py

RUN chmod +x /root/tankutility_exporter.py
RUN mkdir /root/config

COPY config-sample /root/.tank-utility-login

CMD [ "/root/tankutility_exporter.py" ]
