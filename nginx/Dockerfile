FROM nginx:1.24.0

# Utilities
RUN apt-get update && apt-get -y install curl

COPY nginx.conf /etc/nginx/nginx.conf
COPY scripts/* /opt/