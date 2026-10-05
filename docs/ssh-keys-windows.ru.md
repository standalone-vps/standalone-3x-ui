# SSH-ключ в Windows

[English version](ssh-keys-windows.md)

Создайте ключ в **PowerShell**. Запускайте установщик Ansible в **Ubuntu под WSL**.

```text
Ключ в PowerShell → копия в Ubuntu → SSH к VPS → установка из Ubuntu
```

1. Откройте **PowerShell**. Создайте ключ:

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
   ssh-keygen.exe -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519"
   ```

   Дважды введите парольную фразу. Если ключ уже есть, ответьте **no** на запрос о замене. Если команда `ssh-keygen.exe` не найдена, установите OpenSSH Client в PowerShell от имени администратора:

   ```powershell
   Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
   ```

2. Покажите публичный ключ **в PowerShell**:

   ```powershell
   Get-Content "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519.pub"
   ```

   Скопируйте одну строку с `ssh-ed25519` в файл `authorized_keys` на VPS. Приватный ключ на VPS не копируйте.

3. Установите Ubuntu в WSL, если её нет. Выполните **в PowerShell от имени администратора**:

   ```powershell
   wsl --install -d Ubuntu
   ```

   Перезагрузите Windows, если появится запрос. Откройте **Ubuntu** из меню «Пуск». Создайте пользователя Linux.

4. Скопируйте ключ в домашнюю папку **Ubuntu**. Не заменяйте существующий ключ в WSL:

   ```sh
   windows_profile="$(wslpath "$(cmd.exe /c echo %USERPROFILE% | tr -d '\r')")"
   install -d -m 700 "$HOME/.ssh"
   if [ -e "$HOME/.ssh/standalone_3x_ui_ed25519" ] || [ -e "$HOME/.ssh/standalone_3x_ui_ed25519.pub" ]; then
     echo "В WSL уже есть ключ. Остановитесь и проверьте его."
   else
     install -m 600 "$windows_profile/.ssh/standalone_3x_ui_ed25519" "$HOME/.ssh/standalone_3x_ui_ed25519"
     install -m 644 "$windows_profile/.ssh/standalone_3x_ui_ed25519.pub" "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
   fi
   ```

5. Оставьте `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519` в `.env`. Выполните остальные [шаги установки](../README.ru.md) в Ubuntu.

Для ручного входа из **PowerShell** замените `YOUR_VPS_IP`:

```powershell
ssh.exe -p 22 root@YOUR_VPS_IP
ssh.exe -i "$env:USERPROFILE\.ssh\standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
```

Команда для `ops` работает после добавления публичного ключа на VPS. Установщик Ansible напрямую в PowerShell не работает. Ansible допускает запуск в WSL, но не поддерживает WSL как управляющий компьютер для промышленной среды. Для официально поддерживаемого варианта используйте Linux или виртуальную машину с Linux.

Источники: [ключи OpenSSH от Microsoft](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement), [установка WSL](https://learn.microsoft.com/en-us/windows/wsl/install), [управляющий компьютер Ansible](https://docs.ansible.com/projects/ansible/latest/os_guide/intro_windows.html).
