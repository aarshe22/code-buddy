FROM codercom/code-server:latest

# Install Python3 and other useful tools
USER root

RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

# Switch back to coder user
USER coder

