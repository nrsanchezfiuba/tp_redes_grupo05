# Copyright 2025 Yusuke Iwase
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Source: https://github.com/iwaseyusuke/docker-mininet
# Modified on 2025-03-15

FROM ubuntu:22.04

USER root
WORKDIR /root

COPY ./mininet/ENTRYPOINT.sh /

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dnsutils \
    ifupdown \
    iproute2 \
    iptables \
    iputils-ping \
    mininet \
    net-tools \
    openvswitch-switch \
    openvswitch-testcontroller \
    tcpdump \
    vim \
    x11-xserver-utils \
    xterm \
    && rm -rf /var/lib/apt/lists/* \
    && touch /etc/network/interfaces \
    && chmod +x /ENTRYPOINT.sh \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

COPY uv.lock pyproject.toml* ./

ENV PATH="/root/.local/bin:${PATH}"
RUN uv sync

COPY . /root

ENV PYTHONPATH=src

EXPOSE 6633 6653 6640

ENTRYPOINT ["/ENTRYPOINT.sh"]
