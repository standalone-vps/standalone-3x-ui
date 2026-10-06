# SSH key with Windows and WSL

[Русская версия](ssh-keys-windows.ru.md)

Use Ubuntu in WSL for this installer. Keep the repository and SSH key in the Ubuntu home directory. Run the installer and your Codex or Claude Code agent in this Linux environment.

```text
Windows → Ubuntu in WSL → SSH key → VPS → Ansible installer
```

1. Install Ubuntu in WSL if it is missing. Open **PowerShell as Administrator**:

   ```powershell
   wsl --install -d Ubuntu
   ```

   Restart Windows if asked. Open **Ubuntu** from Start and create a Linux user.

2. In the **Ubuntu terminal**, create the SSH key:

   ```sh
   mkdir -p "$HOME/.ssh"
   chmod 700 "$HOME/.ssh"
   ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/standalone_3x_ui_ed25519"
   ```

   Enter a passphrase twice. If this key already exists, answer **no** to the overwrite prompt. Check that its `.pub` file exists before reusing it.

3. In the **Ubuntu terminal**, display the public key:

   ```sh
   cat "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
   ```

   Copy the line beginning with `ssh-ed25519` to the VPS as described in the [main guide](../README.md). Never copy the private key to the VPS.

4. Keep `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519` in `.env`. Run all remaining [installation steps](../README.md) in Ubuntu.

Keep the repository under the Ubuntu home directory, not `/mnt/c/`. Ansible may refuse the default Windows drive permissions. Ansible can run in WSL, but does not officially support WSL as a production control node. Use a Linux computer or VM if you need that support.

Sources: [Microsoft WSL installation](https://learn.microsoft.com/en-us/windows/wsl/install), [Ansible control node](https://docs.ansible.com/projects/ansible/latest/os_guide/intro_windows.html), [Ansible filesystem permissions](https://docs.ansible.com/projects/team-devtools/guides/ansible/permissions/).
