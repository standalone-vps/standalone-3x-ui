# Manual bootstrap through the provider console

[Русская версия](bootstrap-console.ru.md) · [English README](../README.md)

Use this when the provider console permits root login but root/password SSH is disabled. Keep the provider console open until a separate key-only `ops` connection and `sudo -n true` both work. The example account name is `ops`; replace it with `OPS_USER` from `.env` if needed.

## 1. Prepare the local key and verify the VPS host key

First create a key **on your own computer**, following the separate [Linux/WSL guide](ssh-keys-linux.md) or [Windows PowerShell guide](ssh-keys-windows.md). Both give the exact commands for showing the public `.pub` key. Keep that **single public-key line** ready to paste in step 2. Never copy the private key to the VPS. If you already have a suitable key, set its path in `.env` as `SSH_KEY_PATH` and display its `.pub` file.

In the provider console, read the VPS SSH host-key fingerprint:

```sh
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

On Linux/WSL, replace `YOUR_VPS_IP` with the VPS address and `22` with its **current** SSH port; then inspect the scanned host-key fingerprint:

```sh
VPS_HOST=YOUR_VPS_IP
SSH_PORT=22
ssh-keyscan -p "$SSH_PORT" -t ed25519 "$VPS_HOST" > /tmp/vps-hostkey.pub
ssh-keygen -lf /tmp/vps-hostkey.pub
```

Only if that fingerprint matches the provider console, check for an older entry with `ssh-keygen -F "$VPS_HOST"` (or `ssh-keygen -F "[$VPS_HOST]:$SSH_PORT"` for a nonstandard port). Resolve any mismatch before continuing. Then add the verified key to the local `known_hosts` file:

```sh
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
cat /tmp/vps-hostkey.pub >> "$HOME/.ssh/known_hosts"
chmod 600 "$HOME/.ssh/known_hosts"
```

Windows PowerShell users can compare the fingerprint at the first SSH connection in the [Windows guide](ssh-keys-windows.md).

## 2. Create the operations account in the console

As root on the VPS:

```sh
adduser --disabled-password --gecos '' ops
usermod -aG sudo ops
install -d -m 0700 -o ops -g ops /home/ops/.ssh
```

If `nano` is missing, install it from the root console with `apt-get update` and `apt-get install -y nano`. Open the authorized-keys file:

```sh
nano /home/ops/.ssh/authorized_keys
```

Paste the **entire public-key line** you displayed on your own computer, starting with `ssh-ed25519`. It must be one line. In `nano`, press **Ctrl+O** (the letter O; “Write Out”), then **Enter** to confirm the filename, then **Ctrl+X** to exit. The `^O` and `^X` hints at the bottom mean Ctrl+O and Ctrl+X. Set permissions and check that the file has exactly one line:

```sh
chown ops:ops /home/ops/.ssh/authorized_keys
chmod 0600 /home/ops/.ssh/authorized_keys
wc -l /home/ops/.ssh/authorized_keys
```

The last command should print `1` before the filename. Now open a separate sudoers file through `visudo`, telling it to use `nano`:

```sh
VISUAL=nano EDITOR=nano visudo -f /etc/sudoers.d/90-standalone-ops
```

Type exactly this **one line** (replace `ops` here too if you chose another account name):

```text
ops ALL=(ALL:ALL) NOPASSWD:ALL
```

Press **Ctrl+O**, **Enter**, then **Ctrl+X**. `visudo` checks the syntax when you exit; if it reports an error, return to the editor and fix it rather than accepting an invalid file. Then run:

```sh
chown root:root /etc/sudoers.d/90-standalone-ops
chmod 0440 /etc/sudoers.d/90-standalone-ops
visudo -cf /etc/sudoers.d/90-standalone-ops
```

The last command must report that the file parsed successfully. If pasting into the provider console does not work, use its clipboard/paste control or type the public-key line carefully; never paste the private key.

## 3. Prove access before changing SSH

From a **new terminal on your computer**, connect on `BOOTSTRAP_SSH_PORT` as `ops` using the private key and run `sudo -n true`. For a Windows PowerShell example, see the [Windows key guide](ssh-keys-windows.md). On Linux/WSL, replace the example IP and port in `ssh -i "$HOME/.ssh/standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP`, then run `sudo -n true` after login. Keep the root provider console available until this succeeds. If it fails, inspect the key line, ownership, modes, SSH configuration, sudoers syntax, and provider firewall from the console.

For the launcher’s `verify-access` command, temporarily set `CHANGE_SSH_PORT=no` and both SSH port values to the current port in `.env`. Restore the intended settings afterward. Continue with `python3 bin/vps.py check-network` and `python3 bin/vps.py deploy --apply`. Do not rerun the automated root bootstrap after the manual account works.

Never put the root password, private key, or panel credentials in tracked files or chat.
