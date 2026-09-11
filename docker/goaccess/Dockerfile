FROM alpine:3.22
RUN apk add --no-cache goaccess
USER 65534:65534
ENTRYPOINT ["goaccess", "--no-global-config", "--log-format=COMBINED", "--no-progress", "--no-term-resolver", "--anonymize-ip", "--ignore-crawlers", "--no-query-string", "--output=html"]
