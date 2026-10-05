# Create an SSH key on Windows

[Русская версия](ssh-keys-windows.ru.md) · [Provider-console bootstrap](bootstrap-console.md)

Run this section in **PowerShell on your Windows computer**, not in the VPS provider console. Windows 10/11 needs the OpenSSH Client installed (`ssh-keygen.exe` should run). These commands create the key for manual SSH access; Ansible and this repository's Python launcher run in Linux or WSL.

1. Create the `.ssh` directory and key pair:

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
   ssh-keygen.exe -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519"
   ```

   Enter and confirm a passphrase. If the key file already exists, **do not overwrite it**: choose another filename and use it consistently below.

2. Display the public key:

   ```powershell
   Get-Content "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519.pub"
   ```

   Copy the **entire single line** beginning with `ssh-ed25519` to the VPS `authorized_keys` file. Never copy the file without `.pub` to the VPS: that is your private key.

3. After creating `ops` in the provider console, test a manual SSH login from PowerShell. Replace `YOUR_VPS_IP` and `22` with the VPS address and its **current** SSH port:

   ```powershell
   ssh.exe -i "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
   ```

   Compare any new host-key fingerprint shown by SSH with `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` in the provider console **before** accepting it. Enter the private-key passphrase on your computer, then run `sudo -n true` on the VPS.

## Using this same key in WSL for deployment

Open a WSL Linux terminal. Replace `WINDOWS_USER` below with the Windows account directory name under `C:\Users` (for example, `Roman`), then run:

```sh
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
cp "/mnt/c/Users/WINDOWS_USER/.ssh/standalone_3x_ui_ed25519" "$HOME/.ssh/standalone_3x_ui_ed25519"
cp "/mnt/c/Users/WINDOWS_USER/.ssh/standalone_3x_ui_ed25519.pub" "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
chmod 600 "$HOME/.ssh/standalone_3x_ui_ed25519"
chmod 644 "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
eval "$(ssh-agent -s)"
ssh-add "$HOME/.ssh/standalone_3x_ui_ed25519"
```

Check that the source path exists before copying. Keep the private copy inside the WSL home directory; do not point `SSH_KEY_PATH` at `/mnt/c/...`. Run the repository from WSL, with `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519` in `.env`. The launcher needs the key in the Linux SSH agent for noninteractive checks. If you prefer, create the key directly in WSL using the [Linux guide](ssh-keys-linux.md) and install **that** public key on the VPS.

Continue with [provider-console bootstrap](bootstrap-console.md).
