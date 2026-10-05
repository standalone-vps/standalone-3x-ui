# When root SSH is unavailable

[Русская версия](bootstrap-console.ru.md)

Use this guide only if the provider blocks `root` login over SSH. For the normal `root`/password SSH case, use the [main guide](../README.md). The commands below create the same `ops` account through the provider's browser console.

```text
Linux key → provider console as root → create ops → test SSH → install
```

1. On your **Linux computer**, create the key and show its public line:

   ```sh
   mkdir -p "$HOME/.ssh"
   chmod 700 "$HOME/.ssh"
   ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/standalone_3x_ui_ed25519"
   cat "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
   ```

   Enter a passphrase. If the key exists, do not overwrite it. Copy the full public line beginning with `ssh-ed25519`.

2. Open the provider's browser console and sign in to the VPS as `root`. Run **on the VPS**:

   ```sh
   adduser --disabled-password --gecos '' ops
   usermod -aG sudo ops
   install -d -m 0700 -o ops -g ops /home/ops/.ssh
   nano /home/ops/.ssh/authorized_keys
   ```

   If `nano` is missing, run `apt-get update` and `apt-get install -y nano`. Paste the single public-key line. Press **Ctrl+O**, **Enter**, then **Ctrl+X**. Run **on the VPS**:

   ```sh
   chown ops:ops /home/ops/.ssh/authorized_keys
   chmod 0600 /home/ops/.ssh/authorized_keys
   wc -l /home/ops/.ssh/authorized_keys
   VISUAL=nano EDITOR=nano visudo -f /etc/sudoers.d/90-standalone-ops
   ```

   The line count must be `1`. In `visudo`, enter `ops ALL=(ALL:ALL) NOPASSWD:ALL`. Press **Ctrl+O**, **Enter**, then **Ctrl+X**. Finish **on the VPS**:

   ```sh
   chown root:root /etc/sudoers.d/90-standalone-ops
   chmod 0440 /etc/sudoers.d/90-standalone-ops
   visudo -cf /etc/sudoers.d/90-standalone-ops
   ```

3. Keep the console open. In that console, run `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` and note the fingerprint. On your **Linux computer**, test SSH on the VPS's current port:

   ```sh
   ssh -i "$HOME/.ssh/standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
   ```

   On the VPS, run `sudo -n true`. It must finish without a password prompt. Compare any new SSH host fingerprint with the one you noted before accepting it.

4. Return to the [main guide](../README.md) at **step 2** to fill `.env`. Then follow **step 5** to install. Step 3 in that guide is already complete. Keep the provider console available until the new SSH port works.

Never paste the private key or root password into a repository file.
