ARG BUILD_FROM
FROM $BUILD_FROM

# python3 only -- server.py is stdlib-only (http.server, urllib.request,
# json), no pip packages needed at all.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY server.py /server.py
COPY test.html /test.html
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
