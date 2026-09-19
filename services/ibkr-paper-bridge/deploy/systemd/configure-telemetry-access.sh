#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="/etc/take-two/ibkr-telemetry.env"
SERVICE="take-two-ibkr-telemetry.service"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this helper with sudo." >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Telemetry environment is not installed." >&2
  exit 1
fi

read -r -p "Cloudflare Access Client ID: " access_client_id
read -r -s -p "Cloudflare Access Client Secret: " access_client_secret
echo

if [[ ! "${access_client_id}" =~ ^[A-Za-z0-9._-]{10,200}$ ]]; then
  echo "Invalid Access Client ID format." >&2
  exit 1
fi
if [[ ! "${access_client_secret}" =~ ^[A-Za-z0-9._-]{20,300}$ ]]; then
  echo "Invalid Access Client Secret format." >&2
  exit 1
fi

umask 077
temporary_file="$(mktemp /etc/take-two/ibkr-telemetry.env.XXXXXX)"
cleanup() {
  rm -f "${temporary_file}"
  unset access_client_id access_client_secret
}
trap cleanup EXIT

while IFS= read -r line || [[ -n "${line}" ]]; do
  case "${line}" in
    CF_ACCESS_CLIENT_ID=*)
      printf 'CF_ACCESS_CLIENT_ID=%s\n' "${access_client_id}"
      ;;
    CF_ACCESS_CLIENT_SECRET=*)
      printf 'CF_ACCESS_CLIENT_SECRET=%s\n' "${access_client_secret}"
      ;;
    *)
      printf '%s\n' "${line}"
      ;;
  esac
done < "${ENV_FILE}" > "${temporary_file}"

chown root:root "${temporary_file}"
chmod 0600 "${temporary_file}"
mv "${temporary_file}" "${ENV_FILE}"
unset access_client_id access_client_secret

if grep -q 'PASTE_' "${ENV_FILE}"; then
  echo "A required placeholder remains; service not started." >&2
  exit 1
fi

systemctl enable --now "${SERVICE}"
sleep 3
if ! systemctl is-active --quiet "${SERVICE}"; then
  echo "Telemetry service did not remain active." >&2
  journalctl -u "${SERVICE}" -n 20 --no-pager >&2
  exit 1
fi

echo "TELEMETRY_SERVICE_ACTIVE"
journalctl -u "${SERVICE}" -n 5 --no-pager
