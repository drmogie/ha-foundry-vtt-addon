# Foundry VTT Home Assistant add-on.
# Wraps the community felddy/foundryvtt image. Foundry itself is NOT included;
# the container downloads it at first start using your foundryvtt.com account.
ARG FOUNDRY_MAJOR=14
FROM ghcr.io/felddy/foundryvtt:${FOUNDRY_MAJOR}

USER root

COPY run.sh /usr/local/bin/ha-run.sh
RUN chmod a+x /usr/local/bin/ha-run.sh

# Keep the original Foundry start command from the base image.
ENTRYPOINT ["/usr/local/bin/ha-run.sh"]
CMD ["resources/app/main.mjs", "--port=30000", "--headless", "--noupdate", "--dataPath=/data"]
