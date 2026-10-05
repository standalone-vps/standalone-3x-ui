# Если вход root по SSH запрещён

[English version](bootstrap-console.md)

Используйте эту инструкцию, только если провайдер запретил вход `root` по SSH. Если `root` входит по SSH с паролем, откройте [основное руководство](../README.ru.md). Команды ниже создают того же пользователя `ops` через браузерную консоль провайдера.

```text
Ключ в Linux → консоль провайдера как root → создание ops → проверка SSH → установка
```

1. **На компьютере с Linux** создайте ключ и покажите публичную строку:

   ```sh
   mkdir -p "$HOME/.ssh"
   chmod 700 "$HOME/.ssh"
   ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/standalone_3x_ui_ed25519"
   cat "$HOME/.ssh/standalone_3x_ui_ed25519.pub"
   ```

   Придумайте парольную фразу. Если ключ уже существует, не перезаписывайте его. Скопируйте всю публичную строку, которая начинается с `ssh-ed25519`.

2. Откройте браузерную консоль провайдера и войдите на VPS как `root`. Выполните **на VPS**:

   ```sh
   adduser --disabled-password --gecos '' ops
   usermod -aG sudo ops
   install -d -m 0700 -o ops -g ops /home/ops/.ssh
   nano /home/ops/.ssh/authorized_keys
   ```

   Если `nano` отсутствует, выполните `apt-get update` и `apt-get install -y nano`. Вставьте одну строку публичного ключа. Нажмите **Ctrl+O**, **Enter**, затем **Ctrl+X**. Выполните **на VPS**:

   ```sh
   chown ops:ops /home/ops/.ssh/authorized_keys
   chmod 0600 /home/ops/.ssh/authorized_keys
   wc -l /home/ops/.ssh/authorized_keys
   VISUAL=nano EDITOR=nano visudo -f /etc/sudoers.d/90-standalone-ops
   ```

   Число строк должно быть `1`. В `visudo` введите `ops ALL=(ALL:ALL) NOPASSWD:ALL`. Нажмите **Ctrl+O**, **Enter**, затем **Ctrl+X**. Завершите **на VPS**:

   ```sh
   chown root:root /etc/sudoers.d/90-standalone-ops
   chmod 0440 /etc/sudoers.d/90-standalone-ops
   visudo -cf /etc/sudoers.d/90-standalone-ops
   ```

3. Оставьте консоль открытой. Выполните там `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` и запишите отпечаток. **На компьютере с Linux** проверьте SSH на текущем порту VPS:

   ```sh
   ssh -i "$HOME/.ssh/standalone_3x_ui_ed25519" -p 22 ops@YOUR_VPS_IP
   ```

   На VPS выполните `sudo -n true`. Команда должна закончиться без запроса пароля. Если SSH показывает новый отпечаток сервера, сравните его с записанным отпечатком до подтверждения.

4. Вернитесь к [основному руководству](../README.ru.md) на **шаг 2** для заполнения `.env`. Затем перейдите к **шагу 5** для установки. Шаг 3 уже выполнен. Сохраняйте доступ к консоли провайдера, пока не проверите новый SSH-порт.

Не записывайте приватный ключ или пароль `root` в файлы репозитория.
