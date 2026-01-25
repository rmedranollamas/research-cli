#!/bin/bash

# Simple installer for research-cli
#
# Downloads and installs the research binary into /usr/local/bin
#
# Command to use to install research:
# curl -s https://raw.githubusercontent.com/rmedranollamas/research-cli/main/install.sh | sudo bash

set -euo pipefail

# Configuration
readonly PACKAGE="research"
readonly REPO_OWNER="rmedranollamas"
readonly REPO_NAME="research-cli"
readonly DEFAULT_INSTALLATION_DIR="/usr/local/bin"

# Detect OS
OS_TYPE=$(uname -s | tr '[:upper:]' '[:lower:]')
case "$OS_TYPE" in
  linux*)   ARTIFACT_OS="linux" ;;
  darwin*)  ARTIFACT_OS="darwin" ;;
  *)        echo "Error: Unsupported OS type: $OS_TYPE"; exit 1 ;;
esac

# Detect Architecture
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)      ARTIFACT_ARCH="amd64" ;;
  arm64|aarch64) ARTIFACT_ARCH="arm64" ;;
  *)           echo "Error: Unsupported architecture: $ARCH"; exit 1 ;;
esac

installDir="${1:-$DEFAULT_INSTALLATION_DIR}"

if [[ ! -d $installDir ]]; then
  echo "Installation directory $installDir not found."
  echo "Please pass a valid installation directory as a parameter."
  exit 1
fi

# Ensure python3 is available for JSON parsing
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required for the installation script."
  exit 1
fi

echo "Detected OS: $OS_TYPE ($ARCH)."

# Get latest release tag
echo -n "Fetching latest release tag from GitHub ... "
LATEST_TAG=$(curl -s "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('tag_name', ''))")

if [ -z "$LATEST_TAG" ]; then
  echo "failed"
  echo "Error: Could not find latest release for $REPO_OWNER/$REPO_NAME."
  exit 1
fi
echo "$LATEST_TAG"

# Asset naming convention: research-{os}-{arch}
DOWNLOAD_URL="https://github.com/$REPO_OWNER/$REPO_NAME/releases/download/$LATEST_TAG/research-$ARTIFACT_OS-$ARTIFACT_ARCH"

echo -n "Downloading $PACKAGE $LATEST_TAG ... "
TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT

http_code=$(curl -L -s -w "%{http_code}" -o "$TMP_FILE" "$DOWNLOAD_URL")
if [[ $http_code != 200 ]]; then
  echo "failed (HTTP $http_code)"
  echo "Error: Could not download binary. The asset for $ARTIFACT_OS-$ARTIFACT_ARCH might not be available yet."
  exit 1
fi
echo "done"

echo -n "Installing $PACKAGE into $installDir ... "
chmod +x "$TMP_FILE"

# Move binary with appropriate permissions
if [ -w "$installDir" ]; then
    mv "$TMP_FILE" "$installDir/$PACKAGE"
else
    sudo mv "$TMP_FILE" "$installDir/$PACKAGE"
fi
echo "done"

echo ""
echo "$PACKAGE installation complete."
echo "Run '$PACKAGE --help' to verify."
