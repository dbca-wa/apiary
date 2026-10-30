# Prepare the base environment.
FROM ghcr.io/dbca-wa/apiary:latest AS builder_base_apiarydev

USER root

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    g++ \
    libreadline-dev \    
    screen \
    ssh \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN openssl req -new -newkey rsa:4096 -days 3650 -nodes -x509 \
    -subj "/C=AU/ST=Western Australia/L=Perth/O=Development Environment/OU=IT Department/CN=example.com" \
    -keyout /etc/ssl/private/selfsignedssl.key -out /etc/ssl/private/selfsignedssl.crt

RUN cat >> /etc/bash.bashrc <<'BASHRC'
if ! [ -n "${SUDO_USER}" -a -n "${SUDO_PS1}" ]; then
export PS1='\[\e[0;31mdev:\e[0;32m \u@\h:~ \e[0;34m\W\$\e\[\e[0m\] '
fi
BASHRC

# For Linux: create container user/group and prepare home in a single layer
RUN groupadd -g 20000 container \
    && useradd -g 20000 -u 200000 -m -d /home/container -s /bin/bash container \
    && cp /root/.bashrc /home/container || true \
    && cp /root/.profile /home/container || true \
    && chown -R container:container /home/container

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
