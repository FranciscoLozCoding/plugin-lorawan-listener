#!/usr/bin/env bash
#
# Connect to Loriot WebSocket and write each received message to a new file in
# INBOX_DIR. The lorawan-listener plugin (with --loriot-inbox-dir set to the same
# path) watches this directory and processes files. Run this on the node (outside
# the plugin pod); the directory must be the same hostPath mounted into the plugin.
#
# Requires: websocat (recommended) or curl with WebSocket support (7.86+).
#   to install on raspberry pi:
#     sudo wget -O /usr/local/bin/websocat \
#     https://github.com/vi/websocat/releases/download/v1.14.1/websocat.aarch64-unknown-linux-musl
#     sudo chmod +x /usr/local/bin/websocat
#     websocat --version
#
# Env:
#   LORIOT_WEBSOCKET_URL  - required, e.g. wss://us1.loriot.io/app?token=...
#   LORIOT_INBOX_DIR      - required, directory to write message files (or LORAWAN_LORIOT_INBOX)
#
set -e

URL="${LORIOT_WEBSOCKET_URL:-}"
INBOX="${LORIOT_INBOX_DIR:-${LORAWAN_LORIOT_INBOX:-}}"

if [[ -z "$URL" ]]; then
  echo "LORIOT_WEBSOCKET_URL is not set" >&2
  exit 1
fi
if [[ -z "$INBOX" ]]; then
  echo "LORIOT_INBOX_DIR or LORAWAN_LORIOT_INBOX is not set" >&2
  exit 1
fi

mkdir -p "$INBOX"

# Redact URL for logging (strip token=...)
SAFE_URL="${URL%%\?*}"
[[ "$URL" == *"token="* ]] && SAFE_URL="${SAFE_URL}?token=***"

write_line() {
  local line="$1"
  [[ -z "$line" ]] && return
  local f="${INBOX}/loriot-$(date +%s.%N)-$$-${RANDOM:-0}.json"
  printf '%s\n' "$line" > "$f"
  echo "Message received, wrote $(basename "$f")" >&2
}

# Prefer websocat; fall back to curl if it supports WebSocket (--ws, curl 7.86+).
check_ws_tool() {
  if command -v websocat &>/dev/null; then
    echo "websocat"
    return
  fi
  if command -v curl &>/dev/null && curl --help 2>/dev/null | grep -q -- '--ws'; then
    echo "curl"
    return
  fi
  return 1
}

run_websocket() {
  case "$WS_TOOL" in
    websocat) websocat -Un "$URL" || true ;;
    curl)     curl -N -s --no-buffer --ws "$URL" 2>/dev/null || true ;;
    *)
      echo "Neither websocat nor curl with --ws found. Install websocat (https://github.com/vi/websocat) or curl 7.86+." >&2
      exit 1
      ;;
  esac
}

WS_TOOL=$(check_ws_tool) || { echo "No WebSocket tool (websocat or curl 7.86+). Install websocat or curl." >&2; exit 1; }

delay=1
max_delay=60

while true; do
  echo "Connecting to Loriot (${SAFE_URL})..."
  while IFS= read -r line; do
    write_line "$line"
  done < <(run_websocket)
  echo "Disconnected; reconnecting in ${delay}s..."
  sleep "$delay"
  delay=$(( delay * 2 ))
  if (( delay > max_delay )); then
    delay=$max_delay
  fi
done
