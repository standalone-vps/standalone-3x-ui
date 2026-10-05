# Set up a new 3x-ui VPS

[Читать по-русски](README.ru.md)

This guide starts with a **Linux computer**, or **Windows with Ubuntu in WSL**, and a **new Ubuntu 24.04 VPS**. You can sign in to the VPS as `root` with a password over SSH. You will create an `ops` account, then install 3x-ui from a Linux terminal.

Run every command in the place named above its code block. A Linux terminal means native Linux or Ubuntu in WSL. Ansible is the program that runs the installation steps over SSH. Do not put passwords or private keys in `.env`.

```text
Linux or Windows/WSL → SSH as root → create ops → test ops → install 3x-ui → test a client
```

## Before you start

You need the VPS IP address, its `root` password, and a domain name pointing to that IP address. This guide uses SSH port `22`; replace it in SSH commands if your provider uses another port. Keep access to your provider's VPS recovery console in case SSH stops working.

On Linux, open a terminal in the repository directory. On Ubuntu or Debian, install the local tools:

```sh
sudo apt update
sudo apt install -y ansible-core openssh-client python3 nano curl
```

Other Linux distributions need the same tools from their own package manager.

### If your computer runs Windows

1. Open **PowerShell as Administrator**. Install Ubuntu in WSL if it is missing:

   ```powershell
   wsl --install -d Ubuntu
   ```

2. Restart Windows if asked. Open **Ubuntu** from the Start menu. Create a Linux user when prompted.
3. In the Ubuntu terminal, install the same tools:

   ```sh
   sudo apt update
   sudo apt install -y ansible-core openssh-client python3 nano curl
   ```

4. Open the repository directory in the Ubuntu terminal. Windows drive `C:` appears under `/mnt/c/`.

All commands after the PowerShell key commands below run in the **Linux or Ubuntu terminal**.

Check that you are in the repository directory:

```sh
ls bin/vps.py
```

This command must display `bin/vps.py`. Run `python3 --version` too. The version must be 3.10 or newer.

## 1. Create an SSH key

An SSH key has two files. The file ending in `.pub` is the **public key**. You will copy its contents to the VPS. The other file is the **private key**; it stays on your computer.

**Linux:** run these commands in the Linux terminal:

```sh
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/standalone_3x_ui_ed25519"
```

**Windows:** run these commands in **PowerShell**. If `ssh-keygen.exe` is missing, run `Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0` in Administrator PowerShell.

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
ssh-keygen.exe -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519"
Get-Content "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519.pub"
```

Enter and confirm a passphrase when asked. If `ssh-keygen` says the file exists, answer **no**. Reuse it only if it is your key and its `.pub` file exists. Otherwise choose another filename in **all later commands** and in `.env`.

On Linux, display the public key:

```sh
cat "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
```

Copy the full line beginning with `ssh-ed25519`. Never copy the private key to the VPS.

**Windows:** copy the key into Ubuntu before installation. Run this block in the **Ubuntu terminal**:

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

The installer uses this WSL copy. Keep `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519` in `.env`.

## 2. Fill in `.env`

`.env` is the settings file for this VPS. The repository ignores the real `.env` file in Git. If it already exists, `cp -n` keeps it.

```sh
cp -n .env.example .env
nano .env
```

Change these values first:

| Setting | Enter |
| --- | --- |
| `DOMAIN` | Your real domain, such as `vpn.example.com`. Its DNS record must point to the VPS IP. |
| `VPS_HOST` | The VPS IP address. |
| `PANEL_ALLOWED_CIDRS` | Keep `0.0.0.0/0` to open the panel from any IPv4 address. |

The example already uses `22` for the current SSH port, `2322` for the new SSH port, `39089` for the panel, `38443` for subscriptions, and `443` for VLESS. Hysteria2 uses UDP `443` when `ENABLE_HYSTERIA=yes`. Set `ENABLE_HYSTERIA=no` if you do not want that inbound. To keep SSH on `22`, set `CHANGE_SSH_PORT=no` **and** `SSH_TARGET_PORT=22`. Keep the other ports different as shown.

Save `.env` in `nano`: press **Ctrl+O**, **Enter**, then **Ctrl+X**. `Ctrl+O` uses the letter O.

## 3. Sign in to the VPS as root and create ops

Open a **second Linux or Ubuntu terminal**. Replace `YOUR_VPS_IP` with the address from `VPS_HOST`:

```sh
ssh -p 22 root@YOUR_VPS_IP
```

If SSH shows a new server fingerprint, compare it with the fingerprint supplied by your VPS provider before typing `yes`. Enter the `root` password. You are now **on the VPS**.

Check the operating system:

```sh
cat /etc/os-release
```

Continue only if it says Ubuntu 24.04. Run these commands **on the VPS**:

```sh
adduser --disabled-password --gecos '' ops
usermod -aG sudo ops
install -d -m 0700 -o ops -g ops /home/ops/.ssh
nano /home/ops/.ssh/authorized_keys
```

If `nano` is missing on the VPS, run `apt-get update` and `apt-get install -y nano`, then open the file again. Paste the **one public-key line** from step 1. Do not add another line. Press **Ctrl+O**, **Enter**, then **Ctrl+X**.

Still **on the VPS**, set the file permissions and check its line count:

```sh
chown ops:ops /home/ops/.ssh/authorized_keys
chmod 0600 /home/ops/.ssh/authorized_keys
wc -l /home/ops/.ssh/authorized_keys
```

The last command must start with `1`. Now allow `ops` to use `sudo` without a password:

```sh
VISUAL=nano EDITOR=nano visudo -f /etc/sudoers.d/90-standalone-ops
```

Enter exactly this one line in `nano`:

```text
ops ALL=(ALL:ALL) NOPASSWD:ALL
```

Press **Ctrl+O**, **Enter**, then **Ctrl+X**. If `visudo` reports a syntax error, correct the line. Then run **on the VPS**:

```sh
chown root:root /etc/sudoers.d/90-standalone-ops
chmod 0440 /etc/sudoers.d/90-standalone-ops
visudo -cf /etc/sudoers.d/90-standalone-ops
```

The last command must report that the file parsed successfully. Keep the `root` session open for the next step.

## 4. Test the new account

Open a **third Linux or Ubuntu terminal**. Connect on the current SSH port, which is still `22`:

```sh
ssh -i "$HOME/.ssh/standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
```

After login, run **on the VPS**:

```sh
sudo -n true
exit
```

`sudo -n true` must finish without a password prompt or error. If it fails, fix the public key, permissions, or sudoers file in the still-open `root` session. Once it works, type `exit` in the `root` session too.

## 5. Install 3x-ui from the Linux or Ubuntu terminal

Return to the **first terminal** in the repository directory. Load your key into an SSH agent. The agent lets the installer use a passphrase-protected key:

```sh
eval "$(ssh-agent -s)"
ssh-add "$HOME/.ssh/standalone_3x_ui_ed25519"
```

Before installation, allow these ports in the **provider firewall**, if your provider has one:

| Port | Who needs access |
| --- | --- |
| `22/tcp` | Your computer during setup. Keep it until SSH works on the new port. |
| `2322/tcp` | Your computer after the SSH port changes. |
| `80/tcp` | The public internet, for the certificate. |
| `443/tcp` | Clients using VLESS. |
| `38443/tcp` | Clients fetching subscriptions. |
| `443/udp` | Clients using Hysteria2, only when enabled. |
| `39089/tcp` | The public internet, for the panel. |

Use your chosen `.env` port numbers if you changed the examples. Open the provider ports for **IPv4 only**. The installer configures UFW to block IPv6 traffic except loopback. Do not add a DNS `AAAA` record for this VPS. The installer cannot configure the provider firewall. Once SSH works on `2322`, remove the old `22/tcp` provider rule if you changed ports.

Run these commands **in your Linux or Ubuntu terminal**, one at a time:

1. Display the settings and check the ports:

   ```sh
   python3 bin/vps.py plan
   ```

2. Check access and preview firewall changes. This command does not change the VPS:

   ```sh
   python3 bin/vps.py check-network
   ```

3. Install 3x-ui. This command changes the VPS and moves SSH to the selected port:

   ```sh
   python3 bin/vps.py deploy --apply
   ```

4. Check the installed services and ports:

   ```sh
   python3 bin/vps.py verify
   ```

## 6. Open the panel and test a client

After installation, SSH uses the port in `SSH_TARGET_PORT`. For the example settings, run this **in your Linux or Ubuntu terminal**:

```sh
ssh -i "$HOME/.ssh/standalone_3x_ui_ed25519" -p 2322 ops@YOUR_VPS_IP
```

After login, read the credentials **on the VPS**:

```sh
sudo cat /etc/x-ui/install-result.env
```

Read the login details and panel path from that file. Take the domain and panel port from `.env`. Keep the login details private. Open the panel from any IPv4 address. A subscription is an address that gives clients their connection settings.

An inbound is a protocol and port that clients connect to.

1. In the panel, find the VLESS/TLS inbound. Find the Hysteria2 inbound too if you enabled it.
2. Create one test client on each enabled inbound. Copy each client link to a device outside the VPS network.
3. Connect with that device and confirm traffic works. Open its subscription URL and refresh it.
4. Remove the test clients when you finish.

The installer checks services and ports. Only this external client test proves that a real client can connect.

The public website is at `https://DOMAIN/` on port `443`. It shows a small API page. `https://DOMAIN/api/status` returns JSON. The VPS chooses its page from its machine ID. A new VPS gets its own page and node ID; rerunning the playbook keeps the same page. HTTPS traffic reaches Nginx through the VLESS/TLS fallback on local port `8000`. Port `8000` stays closed to the internet.

To update the page on an existing VPS, run this **in your Linux or Ubuntu terminal**:

```sh
python3 bin/vps.py update-page --apply
```

This command updates only the fallback website. It does not recreate the panel or inbounds.

To close IPv6 on an **already installed VPS**, run this in your Linux or Ubuntu terminal:

```sh
python3 bin/vps.py close-ipv6 --apply
python3 bin/vps.py verify
```

UFW blocks IPv6 outside the VPS loopback interface. SSH, the panel and clients continue over IPv4.


## If a command stops

Do not repeat `deploy --apply` without checking the VPS state. The installer can leave completed stages in place. Check SSH on the last working port and run `python3 bin/vps.py verify` when access works. If SSH fails, use the provider recovery console.

The panel version is pinned in `X_UI_VERSION` and the installer playbook. A future release needs a reviewed update; this guide does not select one automatically. This VPS can later become a controller for other 3x-ui nodes, but this installation changes only this VPS.

If your provider blocks `root` login over SSH, use the separate [provider-console procedure](docs/bootstrap-console.md). The [Windows key reference](docs/ssh-keys-windows.md) repeats the PowerShell commands and explains the WSL key copy.
