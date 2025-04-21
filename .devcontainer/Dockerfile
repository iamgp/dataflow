FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Node.js for Evidence and other JS dependencies
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get update \
    && apt-get install -y nodejs \
    && npm install -g npm

# Install uv for Python dependency management
RUN pip install uv

# Install additional system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /workspace

# Create a non-root user to use if preferred
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN if [ "$USERNAME" != "root" ]; then \
    groupadd --gid $USER_GID $USERNAME \
    && useradd -s /bin/bash --uid $USER_UID --gid $USERNAME -m $USERNAME \
    && mkdir -p /home/$USERNAME/.vscode-server /home/$USERNAME/.vscode-server-insiders \
    && chown -R $USERNAME:$USERNAME /home/$USERNAME; \
    fi

# Set the default user
USER $USERNAME
