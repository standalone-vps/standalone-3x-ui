# SSH-ключ в Windows

[English version](ssh-keys-windows.md)

Откройте **PowerShell на компьютере с Windows**. Если команда `ssh-keygen.exe` не найдена, установите компонент Windows OpenSSH Client.

```text
Ключ в PowerShell → публичная строка на VPS → проверка входа по SSH
```

1. Создайте ключ на компьютере с Windows:

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
   ssh-keygen.exe -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519"
   ```

   Придумайте парольную фразу и повторите её. Ответьте **no**, если программа предлагает перезаписать старый ключ.

2. Покажите публичный ключ:

   ```powershell
   Get-Content "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519.pub"
   ```

   Скопируйте **всю одну строку** в файл `authorized_keys` на VPS. Приватный файл не копируйте.

3. После создания `ops` на VPS проверьте вход. Подставьте адрес VPS и при необходимости текущий порт:

   ```powershell
   ssh.exe -i "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
   ```

   На VPS выполните `sudo -n true`. Команда должна закончиться без запроса пароля.

Установщик запускается в Linux или WSL, а не в PowerShell. Если вы используете WSL, создайте ключ **внутри WSL** по [инструкции для Linux](ssh-keys-linux.ru.md). Поместите на VPS публичную строку **этого** ключа. Путь к нему укажите в `SSH_KEY_PATH`. Путь Windows вида `C:\...` для Linux `.env` не подходит.
