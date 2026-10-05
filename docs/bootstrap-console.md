# Manual bootstrap through the provider console

Use this when root/password SSH is disabled but the provider console permits root login. Check the VPS host-key fingerprint in the provider console, enroll the matching key in the controller's `known_hosts` through a manual SSH connection, and keep the console open. Set the account name to the `OPS_USER` chosen in `.env`; the example below uses `ops`.

1. On the controller, run `python3 bin/vps.py keygen` if needed. Display only the **public** key: `cat ~/.ssh/standalone_3x_ui_ed25519.pub`. Never copy the private key to the server.
2. In the VPS provider console as root, create the account: `adduser --disabled-password --gecos '' ops` and `usermod -aG sudo ops`.
3. Create `/home/ops/.ssh` owned by `ops:ops` with mode `0700`. Put the single public-key line in `/home/ops/.ssh/authorized_keys`, owned by `ops:ops` with mode `0600`. You may use `install -d -m 0700 -o ops -g ops /home/ops/.ssh` and then a console editor for `authorized_keys`; verify its contents before changing SSH policy.
4. With `visudo -f /etc/sudoers.d/90-standalone-ops`, add exactly `ops ALL=(ALL:ALL) NOPASSWD:ALL`. Set owner `root:root`, mode `0440`, then run `visudo -cf /etc/sudoers.d/90-standalone-ops`.
5. From a **new controller terminal**, connect on `BOOTSTRAP_SSH_PORT` as `ops` using the private key and run `sudo -n true`. Keep root console access until this works. If it fails, inspect file ownership, permissions, SSH configuration, sudoers syntax, and the provider firewall in the console.
6. Continue with `check-network` and `deploy --apply`. Do not rerun automated root bootstrap after the manual account is working.

Do not paste the root password, private key, or panel credentials into tracked files or chat.
