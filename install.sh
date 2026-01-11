#!/bin/bash

set -e

# Configuration
REPO_OWNER="rmedranollamas"
REPO_NAME="research-cli"
BINARY_NAME="research"
INSTALL_DIR="/usr/local/bin"

# Detect OS
OS_TYPE=$(uname -s | tr '[:upper:]' '[:lower:]')
case "$OS_TYPE" in
  linux*)   ARTIFACT_OS="ubuntu-latest" ;;
  darwin*)  ARTIFACT_OS="macos-latest" ;;
  *)        echo "Error: Unsupported OS type: $OS_TYPE"; exit 1 ;;
esac

echo "Detected OS: $OS_TYPE. Fetching latest release for $ARTIFACT_OS..."

# Get latest release tag
LATEST_TAG=$(curl -s "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest" | sed -nE 's/.*"tag_name": "([^"]+)".*/\1/p')

if [ -z "$LATEST_TAG" ]; then
  echo "Error: Could not find latest release for $REPO_OWNER/$REPO_NAME."
  exit 1
fi

DOWNLOAD_URL="https://github.com/$REPO_OWNER/$REPO_NAME/releases/download/$LATEST_TAG/research-$ARTIFACT_OS"

echo "Downloading $BINARY_NAME version $LATEST_TAG from $DOWNLOAD_URL..."

# Download binary
TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT
curl -L -sf -o "$TMP_FILE" "$DOWNLOAD_URL"
chmod +x "$TMP_FILE"

# Install binary
if [ -w "$INSTALL_DIR" ]; then
    mv "$TMP_FILE" "$INSTALL_DIR/$BINARY_NAME"
else
    echo "Installing to $INSTALL_DIR/$BINARY_NAME (requires sudo)..."
    sudo mv "$TMP_FILE" "$INSTALL_DIR/$BINARY_NAME"
fi

echo "Installation complete. Run 'research --help' to verify."
