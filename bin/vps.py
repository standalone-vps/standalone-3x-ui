#!/usr/bin/env python3
"""Controller-side launcher. Never evaluates .env as shell code."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_KEYS = {
    "DOMAIN", "VPS_HOST", "BOOTSTRAP_SSH_PORT", "OPS_USER", "SSH_KEY_PATH",
    "CHANGE_SSH_PORT", "SSH_TARGET_PORT", "PANEL_PORT", "PANEL_ALLOWED_CIDRS",
    "SUBSCRIPTION_PORT", "VLESS_PORT", "ENABLE_HYSTERIA", "HYSTERIA_PORT",
    "X_UI_VERSION",
}
PORT_KEYS = ("BOOTSTRAP_SSH_PORT", "SSH_TARGET_PORT", "PANEL_PORT", "SUBSCRIPTION_PORT", "VLESS_PORT", "HYSTERIA_PORT")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$")
USER_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


def load_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"Configuration not found: {path}. Copy .env.example to .env first.")
    settings: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line {number}; use KEY=value.")
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key not in ENV_KEYS or key in settings:
            raise ValueError(f"Unknown or duplicate .env key on line {number}: {key}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if any(char in value for char in "\r\n\0"):
            raise ValueError(f"Invalid value for {key}")
        settings[key] = value
    missing = ENV_KEYS - settings.keys()
    if missing:
        raise ValueError(f"Missing .env keys: {', '.join(sorted(missing))}")
    if not DOMAIN_RE.fullmatch(settings["DOMAIN"]):
        raise ValueError("DOMAIN must be a public DNS name, not an IP address")
    host = settings["VPS_HOST"]
    if not host or any(c.isspace() for c in host) or host.startswith("-"):
        raise ValueError("VPS_HOST must be one SSH hostname or IP address")
    if not USER_RE.fullmatch(settings["OPS_USER"]) or settings["OPS_USER"] == "root":
        raise ValueError("OPS_USER must be a non-root Linux account name")
    for name in PORT_KEYS:
        try:
            number = int(settings[name], 10)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc
        if not 1 <= number <= 65535:
            raise ValueError(f"{name} must be in 1..65535")
        settings[name] = str(number)
    for name in ("CHANGE_SSH_PORT", "ENABLE_HYSTERIA"):
        if settings[name].lower() not in ("yes", "no"):
            raise ValueError(f"{name} must be yes or no")
        settings[name] = settings[name].lower()
    cidrs = [part.strip() for part in settings["PANEL_ALLOWED_CIDRS"].split(",")]
    if not cidrs or any(not part for part in cidrs):
        raise ValueError("PANEL_ALLOWED_CIDRS needs at least one source")
    for part in cidrs:
        try:
            net = ipaddress.ip_network(part, strict=False)
        except ValueError as exc:
            raise ValueError(f"Invalid panel CIDR: {part}") from exc
    settings["PANEL_ALLOWED_CIDRS"] = ",".join(cidrs)
    if settings["CHANGE_SSH_PORT"] == "no":
        if settings["SSH_TARGET_PORT"] != settings["BOOTSTRAP_SSH_PORT"]:
            raise ValueError("When CHANGE_SSH_PORT=no, SSH_TARGET_PORT must equal BOOTSTRAP_SSH_PORT")
    else:
        if settings["SSH_TARGET_PORT"] == settings["BOOTSTRAP_SSH_PORT"]:
            raise ValueError("Changing SSH requires a different target port")
    tcp_ports = [int(settings[name]) for name in ("SSH_TARGET_PORT", "PANEL_PORT", "SUBSCRIPTION_PORT", "VLESS_PORT")]
    if len(set(tcp_ports + [80])) != len(tcp_ports) + 1:
        raise ValueError("SSH, panel, subscription, VLESS and ACME TCP 80 ports must be distinct")
    if settings["CHANGE_SSH_PORT"] == "yes" and int(settings["BOOTSTRAP_SSH_PORT"]) in tcp_ports[1:] + [80]:
        raise ValueError("Current SSH port conflicts with a planned TCP service")
    if not settings["X_UI_VERSION"].startswith("v") or settings["X_UI_VERSION"] not in ("v3.9.0",):
        raise ValueError("X_UI_VERSION must be an exact reviewed tag supported by the installer")
    key = Path(settings["SSH_KEY_PATH"]).expanduser()
    if not key.is_absolute():
        raise ValueError("SSH_KEY_PATH must expand to an absolute path")
    settings["SSH_KEY_PATH"] = str(key)
    return settings


def plan(config: dict[str, str]) -> None:
    ssh_port = config["SSH_TARGET_PORT"]
    print(f"Target: {config['VPS_HOST']} ({config['DOMAIN']}); Ubuntu 24.04, SQLite, 3x-ui {config['X_UI_VERSION']}")
    print(f"Bootstrap: root/password on TCP {config['BOOTSTRAP_SSH_PORT']} -> {config['OPS_USER']}/SSH key + sudo -n")
    print(f"Final SSH: TCP {ssh_port}; change: {config['CHANGE_SSH_PORT']}")
    print(f"Public TCP: 80 (ACME), {config['VLESS_PORT']} (VLESS TLS), {config['SUBSCRIPTION_PORT']} (subscription)")
    print(f"Public UDP: {config['HYSTERIA_PORT']} (Hysteria2)" if config["ENABLE_HYSTERIA"] == "yes" else "Hysteria2 disabled; no UDP allow")
    panel_scope = "public IPv4" if "0.0.0.0/0" in config["PANEL_ALLOWED_CIDRS"].split(",") else config["PANEL_ALLOWED_CIDRS"]
    print(f"Panel TCP {config['PANEL_PORT']} allowed from {panel_scope}")
    if ssh_port == "22":
        print("WARNING: Final SSH port 22 is an explicit exception to the source fleet policy.")
    print("Check provider firewall, public DNS, provider console and external client reachability before applying.")


def key_paths(config: dict[str, str]) -> tuple[Path, Path]:
    private = Path(config["SSH_KEY_PATH"])
    return private, Path(str(private) + ".pub")


def generate_key(config: dict[str, str]) -> None:
    private, public = key_paths(config)
    if private.exists() or public.exists():
        raise ValueError("Key path already exists. Reuse it or choose another path; no key was overwritten.")
    private.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-a", "100", "-f", str(private)], check=True)
    print(f"Key created. Install only {public} on the VPS; keep {private} local.")


def require_key(config: dict[str, str]) -> str:
    private, public = key_paths(config)
    if not private.is_file() or not public.is_file():
        raise ValueError("SSH key pair missing. Run keygen or set SSH_KEY_PATH to an existing pair.")
    value = public.read_text(encoding="utf-8").strip()
    if not re.match(r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp[0-9]+) ", value):
        raise ValueError("SSH public key has an unsupported format")
    return value


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("Running:", " ".join(command[:3]), "...", flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def ssh_probe(config: dict[str, str], port: str) -> None:
    private, _ = key_paths(config)
    run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
         "-i", str(private), "-p", port, f"{config['OPS_USER']}@{config['VPS_HOST']}", "sudo -n true"])


def ansible(config: dict[str, str], playbook: str, vars_extra: dict[str, object], *, root_login: bool = False, check: bool = False) -> None:
    if shutil.which("ansible-playbook") is None:
        raise ValueError("ansible-playbook is missing. Install ansible-core on the controller.")
    private, _ = key_paths(config)
    host_vars: dict[str, object] = {
        "ansible_host": config["VPS_HOST"],
        "ansible_user": "root" if root_login else config["OPS_USER"],
        "ansible_port": int(config["BOOTSTRAP_SSH_PORT"] if root_login else vars_extra.get("connection_port", config["SSH_TARGET_PORT"])),
        "ansible_ssh_private_key_file": str(private) if not root_login else None,
    }
    host_vars = {k: v for k, v in host_vars.items() if v is not None}
    inventory = {"all": {"hosts": {"standalone": host_vars}}}
    common: dict[str, object] = {
        "ops_user": config["OPS_USER"], "current_ssh_port": int(config["BOOTSTRAP_SSH_PORT"]),
        "target_ssh_port": int(config["SSH_TARGET_PORT"]), "panel_port": int(config["PANEL_PORT"]),
        "panel_allowed_cidrs": config["PANEL_ALLOWED_CIDRS"].split(","),
        "subscription_port": int(config["SUBSCRIPTION_PORT"]), "vless_port": int(config["VLESS_PORT"]),
        "enable_hysteria": config["ENABLE_HYSTERIA"] == "yes", "hysteria_port": int(config["HYSTERIA_PORT"]),
        "public_hostname": config["DOMAIN"], "x_ui_db_backend": "sqlite",
    }
    common.update(vars_extra)
    common.pop("connection_port", None)
    environment = os.environ.copy()
    environment["ANSIBLE_CONFIG"] = str(ROOT / "ansible.cfg")
    with tempfile.TemporaryDirectory(prefix="standalone-vps-") as directory:
        os.chmod(directory, 0o700)
        inv, extra = Path(directory) / "inventory.json", Path(directory) / "vars.json"
        inv.write_text(json.dumps(inventory), encoding="utf-8")
        extra.write_text(json.dumps(common), encoding="utf-8")
        os.chmod(inv, 0o600)
        os.chmod(extra, 0o600)
        command = ["ansible-playbook", "-i", str(inv), str(ROOT / "ansible/playbooks" / playbook),
                   "--limit", "standalone", "-e", "@" + str(extra)]
        if root_login:
            command.append("--ask-pass")
        if check:
            command += ["--check", "--diff"]
        run(command, env=environment)


STAGES = ("network", "install", "token", "fallback", "cert", "subscription", "vless", "hysteria", "verify")


def deploy(config: dict[str, str], *, check: bool, start: str = "network") -> None:
    if check and start != "network":
        raise ValueError("check-network only supports the network stage")
    require_key(config)
    bootstrap_port = config["BOOTSTRAP_SSH_PORT"]
    target_port = config["SSH_TARGET_PORT"]
    if start == "network":
        ssh_probe(config, bootstrap_port)
        ansible(config, "readiness.yml", {"connection_port": int(bootstrap_port)})
        ansible(config, "network.yml", {"connection_port": int(bootstrap_port), "network_approved": True}, check=check)
        if check:
            print("Check mode stopped before changing SSH connection and panel state.")
            return
        ssh_probe(config, target_port)
        ansible(config, "ssh-cutover.yml", {"connection_port": int(target_port), "cutover_approved": True})
    else:
        ssh_probe(config, target_port)
    ssh_probe(config, target_port)
    panel_vars = {"connection_port": int(target_port), "x_ui_version": config["X_UI_VERSION"], "panel_port": int(config["PANEL_PORT"])}
    active = STAGES[STAGES.index(start):]
    for stage in active:
        print(f"Stage: {stage}", flush=True)
        if stage == "install":
            ansible(config, "3x-ui-install.yml", panel_vars)
        elif stage == "token":
            ansible(config, "3x-ui-api-token.yml", {**panel_vars, "allow_x_ui_api_token_apply": True, "x_ui_api_token_allowed_nodes": ["standalone"]})
        elif stage == "fallback":
            ansible(config, "proxy-fallback-nginx.yml", {**panel_vars, "allow_proxy_fallback_nginx": True})
        elif stage == "cert":
            ansible(config, "3x-ui-cert-panel.yml", {**panel_vars, "allow_x_ui_certificate_apply": True,
                    "x_ui_domain": config["DOMAIN"]})
        elif stage == "subscription":
            ansible(config, "3x-ui-subscription-controller-port.yml", {**panel_vars, "x_ui_subscription_port": int(config["SUBSCRIPTION_PORT"]),
                    "x_ui_subscription_controller_alias": "standalone", "allow_x_ui_subscription_port_apply": True})
        elif stage == "vless":
            ansible(config, "3x-ui-vless-tls-api-inbound.yml", {**panel_vars, "allow_x_ui_vless_tls_api_inbound_apply": True,
                    "x_ui_vless_tls_api_allowed_nodes": ["standalone"], "x_ui_domain": config["DOMAIN"], "x_ui_inbound_port": int(config["VLESS_PORT"])})
        elif stage == "hysteria" and config["ENABLE_HYSTERIA"] == "yes":
            ansible(config, "3x-ui-hysteria-api-inbounds.yml", {**panel_vars, "allow_x_ui_hysteria_api_inbounds_apply": True,
                    "x_ui_hysteria_api_allowed_nodes": ["standalone"], "x_ui_domain": config["DOMAIN"],
                    "x_ui_hysteria_inbounds": [{"remark": f"standalone_hy2_{config['HYSTERIA_PORT']}",
                                                "port": int(config["HYSTERIA_PORT"]), "udp_idle_timeout": 60}]})
        elif stage == "verify":
            ansible(config, "verify.yml", panel_vars)
    print("Deployment playbooks completed. Perform the external client and subscription acceptance checks in README.md.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "keygen", "bootstrap", "deploy", "check-network", "verify-access", "verify"])
    parser.add_argument("--env", type=Path, default=ROOT / ".env")
    parser.add_argument("--apply", action="store_true", help="Required for mutating actions")
    parser.add_argument("--from-stage", choices=STAGES, default="network", help="Resume after inspecting live state")
    args = parser.parse_args()
    try:
        config = load_env(args.env)
        if args.action == "plan":
            plan(config)
        elif args.action == "keygen":
            generate_key(config)
        elif args.action == "bootstrap":
            if not args.apply:
                raise ValueError("Bootstrap changes the VPS; pass --apply after reviewing plan")
            key = require_key(config)
            ansible(config, "bootstrap.yml", {"bootstrap_approved": True, "ops_public_key": key}, root_login=True)
            ssh_probe(config, config["BOOTSTRAP_SSH_PORT"])
        elif args.action == "verify-access":
            require_key(config)
            ssh_probe(config, config["SSH_TARGET_PORT"])
        elif args.action == "verify":
            require_key(config)
            ssh_probe(config, config["SSH_TARGET_PORT"])
            ansible(config, "verify.yml", {"connection_port": int(config["SSH_TARGET_PORT"])})
        else:
            if args.action == "deploy" and not args.apply:
                raise ValueError("Deployment changes the VPS; pass --apply after reviewing plan")
            deploy(config, check=args.action == "check-network", start=args.from_stage)
        return 0
    except (ValueError, subprocess.CalledProcessError, OSError, socket.error) as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
