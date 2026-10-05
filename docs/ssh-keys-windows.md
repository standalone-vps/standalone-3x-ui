# SSH key on Windows

[Русская версия](ssh-keys-windows.ru.md)

Use **PowerShell** to create the key. Use **Ubuntu in WSL** for the Ansible installer.

```text
PowerShell key → copy into Ubuntu → SSH to VPS → run installer in Ubuntu
```

1. Open **PowerShell**. Create the key:

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
   ssh-keygen.exe -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519"
   ```

   Enter a passphrase twice. If the key exists, answer **no** to the overwrite prompt. If `ssh-keygen.exe` is missing, install the Windows OpenSSH Client in Administrator PowerShell:

   ```powershell
   Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
   ```

2. Show the public key in **PowerShell**:

   ```powershell
   Get-Content "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519.pub"
   ```

   Copy the one line beginning with `ssh-ed25519` to the VPS `authorized_keys` file. Never copy the private key to the VPS.

3. Install Ubuntu in WSL if it is missing. Run in **Administrator PowerShell**:

   ```powershell
   wsl --install -d Ubuntu
   ```

   Restart Windows if asked. Open **Ubuntu** from Start and create a Linux user.

4. In the **Ubuntu terminal**, copy the key into its Linux home. Do not replace an existing WSL key:

   ```sh
   windows_profile="$(wslpath "$(cmd.exe /c echo %USERPROFILE% | tr -d '\r')")"
   install -d -m 700 "$HOME/.ssh"
   if [ -e "$HOME/.ssh/standalone_3x_ui_ed25519" ] || [ -e "$HOME/.ssh/standalone_3x_ui_ed25519.pub" ]; then
     echo "A key already exists in WSL. Stop and inspect it."
   else
     install -m 600 "$windows_profile/.ssh/standalone_3x_ui_ed25519" "$HOME/.ssh/standalone_3x_ui_ed25519"
     install -m 644 "$windows_profile/.ssh/standalone_3x_ui_ed25519.pub" "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
   fi
   ```

5. Keep `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519` in `.env`. Run the remaining [installation steps](../README.md) in Ubuntu.

For manual access from **PowerShell**, replace `YOUR_VPS_IP`:

```powershell
ssh.exe -p 22 root@YOUR_VPS_IP
ssh.exe -i "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
```

The `ops` command works after you add the public key to the VPS. The Ansible installer cannot run directly in PowerShell. Ansible documents WSL as runnable, but does not support it as a production control node; use a Linux computer or VM if you need that support.

Sources: [Microsoft OpenSSH keys](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement), [Microsoft WSL installation](https://learn.microsoft.com/en-us/windows/wsl/install), [Ansible control node](https://docs.ansible.com/projects/ansible/latest/os_guide/intro_windows.html).
