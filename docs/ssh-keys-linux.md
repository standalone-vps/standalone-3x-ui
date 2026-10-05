# SSH key on Linux

[Русская версия](ssh-keys-linux.ru.md)

Run these commands **on your Linux computer**. The private key stays there. The public key ends in `.pub`.

```text
Create key → copy public line → add private key to SSH agent
```

1. Create the key:

   ```sh
   mkdir -p "$HOME/.ssh"
   chmod 700 "$HOME/.ssh"
   ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/standalone_3x_ui_ed25519"
   ```

   Enter and confirm a passphrase. If the file exists, answer **no**. Reuse it only if it is your key and its `.pub` file exists. Otherwise change the filename in all later commands and in `.env`.

2. Display the public key:

   ```sh
   cat "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
   ```

   Copy its **one full line** to `/home/ops/.ssh/authorized_keys` on the VPS. Never put the private-key file there.

3. Prepare the private key for the installer:

   ```sh
   eval "$(ssh-agent -s)"
   ssh-add "$HOME/.ssh/standalone_3x_ui_ed25519"
   ```

   Enter the passphrase on your computer. Use `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519` in `.env` for this filename.

The [main guide](../README.md) gives the complete VPS setup in one place.
