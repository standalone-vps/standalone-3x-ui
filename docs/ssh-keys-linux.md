# Create an SSH key on Linux

[Русская версия](ssh-keys-linux.ru.md) · [Provider-console bootstrap](bootstrap-console.md)

Run these commands in a terminal **on your Linux computer**, not in the VPS provider console. If you use Windows Subsystem for Linux (WSL) to run this repository, use its Linux terminal and follow these same steps.

1. Create a private `.ssh` directory and a new Ed25519 key pair:

   ```sh
   mkdir -p "$HOME/.ssh"
   chmod 700 "$HOME/.ssh"
   ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/standalone_3x_ui_ed25519"
   ```

   Enter a passphrase when asked and confirm it. If the file already exists, **do not overwrite it**: choose another filename and set that absolute path in `.env` as `SSH_KEY_PATH`.

2. Display the public key:

   ```sh
   cat "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
   ```

   Copy the **entire single line** beginning with `ssh-ed25519` for the VPS `authorized_keys` file. The file without `.pub` is private: keep it on your computer and never paste it into the provider console or a repository.

3. Add the passphrase-protected private key to an SSH agent before running the launcher:

   ```sh
   eval "$(ssh-agent -s)"
   ssh-add "$HOME/.ssh/standalone_3x_ui_ed25519"
   ```

   Enter the passphrase locally. Keep `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519` in `.env` when using this filename. The launcher uses noninteractive SSH checks, so a protected key must be available in the agent.

Continue with [provider-console bootstrap](bootstrap-console.md). If the provider permits root/password SSH, the automated bootstrap described in the [README](../README.md) can install the public key instead.
