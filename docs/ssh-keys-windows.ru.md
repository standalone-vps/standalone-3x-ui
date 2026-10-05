# Создание SSH-ключа в Windows

[English version](ssh-keys-windows.md) · [Настройка через консоль провайдера](bootstrap-console.ru.md)

Выполняйте команды в **PowerShell на компьютере с Windows**, не в консоли VPS. В Windows 10/11 должен быть установлен компонент OpenSSH Client (команда `ssh-keygen.exe` должна запускаться). Эти команды создают ключ для ручного SSH-доступа; Ansible и Python-установщик из этого репозитория запускаются в Linux или WSL.

1. Создайте каталог `.ssh` и пару ключей:

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
   ssh-keygen.exe -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519"
   ```

   Придумайте парольную фразу, введите её и подтвердите. Если файл ключа уже существует, **не перезаписывайте его**: выберите другое имя и используйте его во всех последующих командах.

2. Покажите публичный ключ:

   ```powershell
   Get-Content "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519.pub"
   ```

   Скопируйте **всю одну строку**, начинающуюся с `ssh-ed25519`, в файл `authorized_keys` на VPS. Файл без `.pub` — приватный ключ; не переносите его на VPS.

3. После создания `ops` в консоли провайдера проверьте ручной вход из PowerShell. Замените `YOUR_VPS_IP` на адрес VPS, а `22` — на его **текущий** SSH-порт:

   ```powershell
   ssh.exe -i "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
   ```

   Если SSH покажет отпечаток нового ключа сервера, сравните его с результатом `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` в консоли провайдера **до** подтверждения. Введите парольную фразу приватного ключа на своём компьютере, затем на VPS выполните `sudo -n true`.

## Использование того же ключа в WSL для установки

Откройте терминал Linux в WSL. Замените `WINDOWS_USER` ниже на имя папки учётной записи Windows в `C:\Users` (например, `Roman`), затем выполните:

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

Перед копированием убедитесь, что исходный путь существует. Храните приватную копию в домашнем каталоге WSL; не указывайте в `SSH_KEY_PATH` путь `/mnt/c/...`. Запускайте репозиторий из WSL, указав в `.env` `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519`. Для автоматических проверок установщику нужен ключ в Linux SSH-агенте. Вы также можете создать ключ прямо в WSL по [инструкции для Linux](ssh-keys-linux.ru.md) и поместить на VPS **его** публичную часть.

Продолжайте по [инструкции для консоли провайдера](bootstrap-console.ru.md).
