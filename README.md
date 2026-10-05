# Standalone 3x-ui VPS

**Documentation in Russian:** [README.ru.md](README.ru.md). The English documentation is the default for this repository.

Ansible control plane for **one new Ubuntu 24.04 VPS**. It starts with provider `root`/password access, establishes a key-only `ops` account with passwordless sudo, then installs a standalone 3x-ui panel, subscription endpoint, VLESS/TLS and optional Hysteria2. This VPS is its own controller; registration of future remote nodes is a later, separate operation.

The source playbooks were adapted from `vps-fleet-ops` at repository creation. They retain explicit single-host scope, exact installer tag plus checksum, local bearer API, SQLite backup, and sanitized outputs. No existing fleet inventory or controller is needed.

## Controller prerequisites

- Python 3.10+, `ansible-core`, OpenSSH client and `ssh-keygen`; `sshpass` is required by Ansible's interactive `--ask-pass` bootstrap mode.
- A new Ubuntu 24.04 VPS with working provider console, initial root/password access through SSH or that console, a public IPv4 address, and enough memory and disk for 3x-ui and Nginx.
- A public DNS name resolving to the VPS. Confirm provider firewall allows the selected SSH, `80/tcp`, VLESS TCP, subscription TCP, and optional Hysteria UDP ports. Panel access should allow only the configured administration CIDRs.
- Review the 3x-ui installer tag and SHA256 in `ansible/playbooks/3x-ui-install.yml` before deployment. This repository pins [`v3.9.0`](https://github.com/MHSanaei/3x-ui/releases/tag/v3.9.0), verified as GitHub's latest stable release on 2026-10-05; it does not silently select a newer release.

Real settings, credentials, backups and exports are excluded from Git. The root password is requested by Ansible at the terminal during bootstrap and is never stored in `.env`. Before bootstrap, compare the VPS SSH host-key fingerprint with the provider console and add the verified key to local `known_hosts`. Use the [console bootstrap guide](docs/bootstrap-console.md) if root SSH is disabled. The launcher uses `StrictHostKeyChecking=yes` and never auto-accepts a new host key.

## First deployment

1. `cp .env.example .env` and edit `.env`. A Russian-commented template is also available as `.env.ru.example`. Choose a separate panel port and subscription port. `VLESS_PORT=443` is TCP; `HYSTERIA_PORT=443` is UDP, so the two may share the number. Set `ENABLE_HYSTERIA=no` to omit Hysteria2 and its UDP rule. If `CHANGE_SSH_PORT=no`, set `SSH_TARGET_PORT` equal to `BOOTSTRAP_SSH_PORT`; retaining SSH `22` is an explicit exception to the source fleet policy.
2. `python3 bin/vps.py plan`. Review the displayed firewall plan, DNS, provider firewall, and console recovery access.
3. Run `python3 bin/vps.py keygen` for a new local key, or point `SSH_KEY_PATH` at an existing key pair. Key generation prompts for a passphrase; add a passphrase-protected key to `ssh-agent` before deployment. The private key never leaves the controller.
4. Run `python3 bin/vps.py bootstrap --apply`. Ansible prompts for the initial root password. If the provider permits root access only through its console, follow [manual console bootstrap](docs/bootstrap-console.md) and then run `python3 bin/vps.py verify-access` after setting `CHANGE_SSH_PORT=no` and both SSH port values to the current port in `.env`. Restore the intended port settings before `check-network`. This creates the operations account, installs **only the public key**, writes a validated `sudoers.d` file, and probes a fresh key-only `sudo -n` login. The old root/password path is still available if this fails.
5. Run `python3 bin/vps.py check-network`, then `python3 bin/vps.py deploy --apply`. Network setup opens both old and selected SSH ports before changing the listener. The launcher verifies the selected port in a separate SSH session, then disables root/password SSH and closes the old port. It then installs 3x-ui, token, loopback Nginx fallback, certificate, subscription, VLESS/TLS and optionally Hysteria2, followed by a local read-only verification.
6. Run `python3 bin/vps.py verify` after installation and after a reboot. Inspect the panel credentials **on the VPS** from `/etc/x-ui/install-result.env` through the verified operations account; do not paste them into Git or chat.

`check-network` is a preview and cannot predict every runtime effect on an untouched host, especially if UFW is not yet installed. Do not mistake a check-mode result for an active listener or reachable provider port. Each mutating playbook uses `--limit standalone`. The launcher passes only non-secret deployment values through a temporary mode-0600 vars file, which is removed after each playbook. API tokens and generated credentials remain on the VPS.

## Client acceptance test

1. Reach the administration panel only from `PANEL_ALLOWED_CIDRS` or through an SSH tunnel. Confirm its certificate and login.
2. In the panel, inspect the VLESS/TLS inbound on the selected TCP port. If enabled, inspect the Hysteria2 inbound on the selected UDP port. Create one temporary client on each selected inbound, then obtain its connection link from the panel.
3. From an **external** client network, import the link and verify authenticated proxy traffic over VLESS/TLS and Hysteria2 (if enabled). Check both IPv4 reachability and the DNS/certificate name.
4. Open the subscription URL shown by the panel, confirm that it contains only the intended clients and protocols, and refresh it from the external client. A local listening port alone does not prove the subscription works.
5. Remove the temporary clients after the test, or explicitly hand their credentials to the administrator. Back up the SQLite database and the certificate material before adding production clients.

The launcher cannot perform the external authenticated client test without a real VPS and a client endpoint. It reports playbook completion separately from this acceptance test.

## Recovery and reruns

The installer refuses to reinstall an existing panel without a separate review, and inbound creation refuses duplicates. This is intentional: `deploy` is a first-deployment path, not a destructive reconciliation loop. After a failed or interrupted stage, **first** verify SSH on the known-good port, `sudo -n`, `sshd -T`, `ssh.socket`, `ufw status`, `systemctl is-active x-ui`, and the local 3x-ui state. Then resume only after inspecting the actual state, for example `python3 bin/vps.py deploy --apply --from-stage cert`. Available stages are `network`, `install`, `token`, `fallback`, `cert`, `subscription`, `vless`, `hysteria`, and `verify`.

If SSH is lost, use the provider console. Check the managed drop-ins under `/etc/ssh/sshd_config.d/` and `/etc/systemd/system/ssh.socket.d/`, validate with `sshd -t`, inspect UFW rules, then restore a known-good port before restarting SSH. If panel mutation fails, inspect the on-host SQLite backups under `/root/` before a reviewed restore. Do not rerun a partly completed inbound creation blindly.

## Future remote nodes

The standalone panel can later become the primary controller for native remote nodes. Before registering one, design its own restricted panel/API access, credentials, client placement and subscription visibility. This first-deployment repository does not automatically register or change any other VPS.

## Repository layout

- `.env.example`: documented non-secret deployment settings.
- `bin/vps.py`: local validation and staged launcher.
- `ansible/playbooks/bootstrap.yml`, `network.yml`, `ssh-cutover.yml`, `verify.yml`: standalone access and host lifecycle.
- `ansible/playbooks/3x-ui-*.yml`, `proxy-fallback-nginx.yml`, `ansible/roles/proxy_fallback_nginx/`: adapted 3x-ui installation and inbound steps.

