# SSH-ключ для Windows и WSL

[English version](ssh-keys-windows.md)

Используйте Ubuntu в WSL для этого установщика. Храните репозиторий и SSH-ключ в домашней папке Ubuntu. Запускайте установщик и агента Codex или Claude Code в этой среде Linux.

```text
Windows → Ubuntu в WSL → SSH-ключ → VPS → установщик Ansible
```

1. Если Ubuntu в WSL ещё нет, откройте **PowerShell от имени администратора**:

   ```powershell
   wsl --install -d Ubuntu
   ```

   Перезагрузите Windows, если появится запрос. Откройте **Ubuntu** из меню «Пуск» и создайте пользователя Linux.

2. Создайте SSH-ключ **в терминале Ubuntu**:

   ```sh
   mkdir -p "$HOME/.ssh"
   chmod 700 "$HOME/.ssh"
   ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/standalone_3x_ui_ed25519"
   ```

   Дважды введите парольную фразу. Если ключ уже существует, ответьте **no** на запрос о замене. Перед повторным использованием проверьте наличие файла `.pub`.

3. Покажите публичный ключ **в терминале Ubuntu**:

   ```sh
   cat "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
   ```

   Скопируйте строку с `ssh-ed25519` на VPS по [основной инструкции](../README.ru.md). Никогда не копируйте приватный ключ на VPS.

4. Оставьте `SSH_KEY_PATH=~/.ssh/standalone_3x_ui_ed25519` в `.env`. Выполните остальные [шаги установки](../README.ru.md) в Ubuntu.

Храните репозиторий в домашней папке Ubuntu, а не в `/mnt/c/`. Ansible может отклонить стандартные права на диске Windows. Ansible запускается в WSL, но официально не поддерживает WSL как управляющий компьютер для промышленной среды. Для официально поддерживаемого варианта используйте Linux или виртуальную машину с Linux.

Источники: [установка WSL от Microsoft](https://learn.microsoft.com/en-us/windows/wsl/install), [управляющий компьютер Ansible](https://docs.ansible.com/projects/ansible/latest/os_guide/intro_windows.html), [права файлов Ansible](https://docs.ansible.com/projects/team-devtools/guides/ansible/permissions/).
