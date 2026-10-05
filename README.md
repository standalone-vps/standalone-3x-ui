# Set up a new 3x-ui VPS

[Читать по-русски](README.ru.md)

This guide starts with a **Linux computer** and a **new Ubuntu 24.04 VPS**. You can sign in to the VPS as `root` with a password over SSH. You will create an `ops` account, then install 3x-ui from your Linux computer.

Run every command in the place named above its code block. Ansible is the program that runs the installation steps over SSH. Do not put passwords or private keys in `.env`.

```text
Linux computer → SSH as root → create ops → test ops → install 3x-ui → test a client
```

## Before you start

You need the VPS IP address, its `root` password, and a domain name pointing to that IP address. This guide uses SSH port `22`; replace it in SSH commands if your provider uses another port. Keep access to your provider's VPS recovery console in case SSH stops working.

Open a terminal **on your Linux computer** in the directory containing this README. If that computer uses Ubuntu or Debian, install the local tools:

```sh
sudo apt update
sudo apt install -y ansible-core openssh-client python3 nano curl
```

Other Linux distributions need the same tools from their own package manager. Check that you are in the repository directory:

```sh
ls bin/vps.py
```

This command must display `bin/vps.py`. Run `python3 --version` too. The version must be 3.10 or newer.

## 1. Create an SSH key on your Linux computer

An SSH key has two files. The file ending in `.pub` is the **public key**. You will copy its contents to the VPS. The other file is the **private key**; it stays on your computer.

```sh
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/standalone_3x_ui_ed25519"
```

Enter and confirm a passphrase when asked. If `ssh-keygen` says the file exists, answer **no**. Reuse it only if it is your key and its `.pub` file exists. Otherwise choose another filename in **all later commands** and in `.env`.

Display the public key and keep this terminal open:

```sh
cat "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
```

Copy the full line beginning with `ssh-ed25519`. Do not copy the private key.

## 2. Fill in `.env` on your Linux computer

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

Open a **second terminal on your Linux computer**. Replace `YOUR_VPS_IP` with the address from `VPS_HOST`:

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

Open a **third terminal on your Linux computer**. Connect on the current SSH port, which is still `22`:

```sh
ssh -i "$HOME/.ssh/standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
```

After login, run **on the VPS**:

```sh
sudo -n true
exit
```

`sudo -n true` must finish without a password prompt or error. If it fails, fix the public key, permissions, or sudoers file in the still-open `root` session. Once it works, type `exit` in the `root` session too.

## 5. Install 3x-ui from your Linux computer

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

Use your chosen `.env` port numbers if you changed the examples. The installer configures the VPS firewall. It cannot configure the provider firewall. Once SSH works on `2322`, remove the old `22/tcp` provider rule if you changed ports.

Run these commands **on your Linux computer**, one at a time:

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

After installation, SSH uses the port in `SSH_TARGET_PORT`. For the example settings, run this **on your Linux computer**:

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

To update the page on an existing VPS, run this **on your Linux computer**:

```sh
python3 bin/vps.py update-page --apply
```

This command updates only the fallback website. It does not recreate the panel or inbounds.


## If a command stops

Do not repeat `deploy --apply` without checking the VPS state. The installer can leave completed stages in place. Check SSH on the last working port and run `python3 bin/vps.py verify` when access works. If SSH fails, use the provider recovery console.

The panel version is pinned in `X_UI_VERSION` and the installer playbook. A future release needs a reviewed update; this guide does not select one automatically. This VPS can later become a controller for other 3x-ui nodes, but this installation changes only this VPS.

If your provider blocks `root` login over SSH, use the separate [provider-console procedure](docs/bootstrap-console.md). If you use Windows, see the [Windows key commands](docs/ssh-keys-windows.md); run the installer in Linux or WSL.
