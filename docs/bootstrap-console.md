# Manual bootstrap through the provider console

[Русская версия](bootstrap-console.ru.md) · [English README](../README.md)

Use this when the provider console permits root login but root/password SSH is disabled. Keep the provider console open until a separate key-only `ops` connection and `sudo -n true` both work. The example account name is `ops`; replace it with `OPS_USER` from `.env` if needed.

## 1. Prepare the local key and verify the VPS host key

On the controller, run `python3 bin/vps.py keygen` if you need a new key. The command creates a private key at `SSH_KEY_PATH` and a `.pub` file beside it. Display only the public key with `cat ~/.ssh/standalone_3x_ui_ed25519.pub` when using the example path. Never copy the private key to the VPS.

In the provider console, read the VPS SSH host-key fingerprint with `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`. On the controller, obtain the public host key with `ssh-keyscan -p <current-ssh-port> -t ed25519 <vps-host> > /tmp/vps-hostkey.pub`, then inspect it with `ssh-keygen -lf /tmp/vps-hostkey.pub`. Add the scanned key to `~/.ssh/known_hosts` **only after the fingerprints match** (for example, `cat /tmp/vps-hostkey.pub >> ~/.ssh/known_hosts` after checking for an existing entry). The host key is public; the comparison prevents trusting an unverified network response. For a nonstandard port, keep the `[host]:port` form produced by `ssh-keyscan`.

## 2. Create the operations account in the console

As root on the VPS:

```sh
adduser --disabled-password --gecos '' ops
usermod -aG sudo ops
install -d -m 0700 -o ops -g ops /home/ops/.ssh
```

With a console editor, put the single local `.pub` line into `/home/ops/.ssh/authorized_keys`. Then set ownership and permissions:

```sh
chown ops:ops /home/ops/.ssh/authorized_keys
chmod 0600 /home/ops/.ssh/authorized_keys
```

Create `/etc/sudoers.d/90-standalone-ops` with exactly `ops ALL=(ALL:ALL) NOPASSWD:ALL` using `visudo -f /etc/sudoers.d/90-standalone-ops`. Set owner `root:root` and mode `0440`, then run `visudo -cf /etc/sudoers.d/90-standalone-ops`.

## 3. Prove access before changing SSH

From a **new controller terminal**, connect on `BOOTSTRAP_SSH_PORT` as `ops` using the private key and run `sudo -n true`. Keep the root provider console available until this succeeds. If it fails, inspect the key line, ownership, modes, SSH configuration, sudoers syntax, and provider firewall from the console.

For the launcher’s `verify-access` command, temporarily set `CHANGE_SSH_PORT=no` and both SSH port values to the current port in `.env`. Restore the intended settings afterward. Continue with `python3 bin/vps.py check-network` and `python3 bin/vps.py deploy --apply`. Do not rerun the automated root bootstrap after the manual account works.

Never put the root password, private key, or panel credentials in tracked files or chat.
