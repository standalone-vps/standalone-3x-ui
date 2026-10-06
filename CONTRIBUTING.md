# Contributing

[Читать по-русски](CONTRIBUTING.ru.md)

This project installs network services on a VPS. Keep changes small and reviewable.

1. Open an issue for a bug or proposed change. Do not include a real IP address, domain, SSH key, password, panel credential, token, client link, subscription URL, or `.env` file.
2. Make the change in a branch. Update both English and Russian instructions when you change a user-facing step.
3. Run the local checks below. They do not connect to a VPS.
4. Open a pull request. Explain the change, the checks you ran, and any effect on SSH, firewall rules, certificates, or existing 3x-ui data.

```sh
python3 -m pip install 'pytest>=8,<9'
python3 -m pytest -q
python3 -m compileall -q bin
```

Never test a pull request by running `deploy --apply` on someone else's VPS. Do not commit live inventory, `.env`, credentials, backups, or exports. See [SECURITY.md](SECURITY.md) to report a vulnerability privately.

Changes to the pinned 3x-ui version need a separate review of upstream release notes and installation behavior. Include the exact version and your validation in the pull request.
