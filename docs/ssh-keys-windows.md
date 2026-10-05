# SSH key on Windows

[Русская версия](ssh-keys-windows.ru.md)

Open **PowerShell on Windows**. Install the Windows OpenSSH Client first if `ssh-keygen.exe` is unavailable.

```text
PowerShell key → public line on VPS → manual SSH login
```

1. Create a key on the Windows computer:

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
   ssh-keygen.exe -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519"
   ```

   Enter and confirm a passphrase. Answer **no** if asked to overwrite an existing key.

2. Display the public key:

   ```powershell
   Get-Content "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519.pub"
   ```

   Copy its **one full line** to the VPS `authorized_keys` file. Do not copy the private-key file.

3. After creating `ops` on the VPS, test access. Replace `YOUR_VPS_IP` and the current port if needed:

   ```powershell
   ssh.exe -i "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
   ```

   On the VPS, run `sudo -n true`. It must finish without asking for a password.

The installer runs on Linux or in WSL, not in PowerShell. If you use WSL, create the installation key **inside WSL** with the [Linux commands](ssh-keys-linux.md). Put **that key's** public line on the VPS and set `SSH_KEY_PATH` to its WSL path. Do not use a Windows `C:\...` path in Linux `.env`.
