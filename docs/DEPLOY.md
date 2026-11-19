# Putting Cumetria on the Oracle server

Step by step, for when the private test on your PC is done. **We do this together**; nothing here has been run on the server yet.

The server already runs the group's game servers: **Dragonwilds** (Docker Compose, UDP 7777 and 8888) and **Minecraft Paper** (Java under GNU screen, TCP 41882). Every step below leaves them alone. Look for the **Game servers** notes: they say what to check, and what never to do.

What you'll need:
- SSH access to the server, as the usual user (on Oracle Ubuntu images that's `ubuntu`).
- The Oracle Cloud console (to open ports).
- A domain name pointing at the server (step 4). Picking one is still an open item in `PLAN.md`.
- An email account that can send the sign-in links (SMTP), and the Google sign-in values from `GOOGLE_SIGN_IN.md`.

---

## 1. Look before touching

Write down how things are now, so you can compare after each step.

```bash
free -h                        # memory: expect ~18 GiB available
df -h /                        # disk: expect ~39 GB free
docker ps                      # Dragonwilds' container(s) should be "Up"
sudo ss -tulpn | grep -E ':(7777|8888|41882|80|443)\b'
screen -ls                     # Minecraft's screen session
docker compose version         # needs "Docker Compose version v2..."
```

The `ss` line should show 7777 and 8888 (UDP, Dragonwilds) and 41882 (TCP, Java), and **nothing on 80 or 443**. If something already uses 80 or 443, stop here and tell Claude.

If `docker compose version` fails but `docker-compose --version` works, the server has the old Compose. Tell Claude before going on: the commands below need the new one.

> **Game servers:** in this guide, every `docker compose` command runs inside `/opt/cumetria` and only affects Cumetria's containers. **Never** run `docker system prune`, `docker volume prune`, or `docker compose down` in the Dragonwilds folder.

## 2. Security updates (Ubuntu Pro)

Ubuntu 20.04 only gets security fixes through **Ubuntu Pro**, free for personal use on up to 5 machines.

1. Sign in at <https://ubuntu.com/pro/dashboard> and copy your token.
2. On the server:
   ```bash
   sudo pro attach YOUR_TOKEN
   sudo pro status              # esm-infra should be "enabled"
   apt list --upgradable
   ```
3. Read the list. If it includes `docker-ce`, `containerd.io` or `docker-ce-cli`, upgrading them **restarts Docker, and with it Dragonwilds**. Do those at a quiet time, and tell the group first.
4. Then upgrade: `sudo apt upgrade`.

> **Game servers:** a **reboot** stops Minecraft. It runs by hand under `screen`, so nothing restarts it. If the update asks for a reboot (`/var/run/reboot-required` exists), plan it with the group and restart Minecraft afterwards the usual way.

## 3. Open ports 80 and 443 (two layers)

Oracle blocks web traffic twice: in the cloud console, and in the server's own firewall.

**a) Oracle console.** *Networking → Virtual cloud networks →* your VCN → *Security lists* → the default list → *Add ingress rules*. Add two rules:
- Source `0.0.0.0/0`, IP protocol TCP, destination port **80**, description "Cumetria http".
- The same with destination port **443**, description "Cumetria https".

Don't change the existing rules (22, 7777, 8888, 41882).

**b) The server's firewall (iptables).** Oracle's Ubuntu image ends its list of allowed traffic with a "reject everything else" rule. New rules must go **above** it.

1. Look at the current rules:
   ```bash
   sudo iptables -L INPUT -n --line-numbers
   ```
   Find the line number of the `REJECT ... reject-with icmp-host-prohibited` rule. Usually it's 6, just after the SSH (port 22) rule.
2. Insert the two rules at that number (here 6). The REJECT rule moves down:
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo iptables -L INPUT -n --line-numbers     # 80 and 443 now come before REJECT
   ```
3. **Make them survive a reboot.** Open the saved rules with `sudo nano /etc/iptables/rules.v4`. Under the line containing `--dport 22 -j ACCEPT`, add:
   ```
   -A INPUT -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT
   -A INPUT -p tcp -m state --state NEW -m tcp --dport 443 -j ACCEPT
   ```
   Save with Ctrl+O, Enter, Ctrl+X.

> **Game servers:** this step **only adds rules**. Don't use `netfilter-persistent save` or `iptables-restore`: the first would also save Docker's temporary rules into the file, and the second would wipe the rules Docker made for Dragonwilds until Docker restarts. Editing the file by hand avoids both.

**To undo:** run `sudo iptables -D INPUT -p tcp -m state --state NEW --dport 80 -j ACCEPT`, then the same with 443. Then remove the two lines from `rules.v4`.

## 4. Domain

At your domain provider, add an **A record** for the name you chose (e.g. `cumetria.example.org`) pointing to the server's public IP. That IP is on the instance's page in the Oracle console.

Check it from your PC: `nslookup cumetria.example.org` should show that IP. It can take from a few minutes to an hour.

## 5. Get the code and write the settings

```bash
sudo mkdir -p /opt/cumetria && sudo chown "$USER": /opt/cumetria
git clone https://github.com/Wolfrag1910/activity_planner.git /opt/cumetria
cd /opt/cumetria
cp .env.example .env
chmod 600 .env                 # only you can read it: it holds secrets
nano .env
```

Values for the server, replacing `cumetria.example.org` with your domain:

| Setting | Server value | Why |
|---|---|---|
| `DJANGO_SECRET_KEY` | a new long random value: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` | Signs sign-in links and sessions. Never reuse your PC's |
| `DJANGO_DEBUG` | `false` | Hides technical error pages |
| `DJANGO_ALLOWED_HOSTS` | `cumetria.example.org` | The site only answers to its own name |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://cumetria.example.org` | Lets forms be sent from the real address |
| `DJANGO_HTTPS` | `true` | Cookies only travel over HTTPS |
| `SITE_ADDRESS` | `cumetria.example.org` | Caddy fetches a free HTTPS certificate for this name |
| `HTTP_PORT` / `HTTPS_PORT` | `80` / `443` | The normal web ports |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | your sending account | Sign-in links really get emailed (still a research item in `BUILD.md`) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | from `GOOGLE_SIGN_IN.md` | Add the server's redirect address there first |

## 6. Start the site

```bash
cd /opt/cumetria
docker compose up -d --build
docker compose ps                         # web should become "healthy" within a minute
docker compose logs caddy | tail -20      # look for "certificate obtained successfully"
```

The first build takes a few minutes; it builds natively for ARM64. Then:

- Open `https://cumetria.example.org/healthz`: it should say `ok`.
- Create your account:
  ```bash
  docker compose exec web python manage.py create_owner --email you@gmail.com --name Alex
  ```
- Sign in at `https://cumetria.example.org`.

If the certificate fails, ports 80/443 or the domain aren't reachable yet: re-check steps 3 and 4. Caddy keeps retrying on its own.

## 7. Check memory and the game servers

```bash
docker stats --no-stream        # cumetria web under 512 MiB, caddy under 128 MiB (their limits)
free -h
docker ps                       # Dragonwilds still "Up"
sudo ss -tulpn | grep -E ':(7777|8888|41882)\b'
screen -ls                      # Minecraft still there
```

Compare with step 1. If friends are online, ask one to join each game server.

## 8. Nightly backup

The `backup_data` command writes one file per night holding the database and the photos. It keeps the last 14. The script `docker/nightly-backup.sh` runs it and copies the files out of Docker into `~/cumetria-backups`.

1. Try it once by hand:
   ```bash
   /opt/cumetria/docker/nightly-backup.sh
   ls -lh ~/cumetria-backups
   ```
2. Run it every night at 04:15:
   ```bash
   crontab -e
   ```
   Add this line, then save:
   ```
   15 4 * * * /opt/cumetria/docker/nightly-backup.sh >> $HOME/cumetria-backup.log 2>&1
   ```
3. **Off the server** (to decide together). A backup on the same machine doesn't help if the machine is lost.
   - **Recommended: Oracle Object Storage.** It's part of the free tier (20 GB). Install `rclone` (`sudo apt install rclone`) and set up a remote called `cumetria-offsite` with `rclone config`. Then uncomment the `rclone copy` line in `docker/nightly-backup.sh`.
   - **Alternative: pull to your PC** now and then: `scp ubuntu@SERVER_IP:~/cumetria-backups/* .`

**Restore drill.** Do it once now, so you know it works when it matters.

1. Stop the site:
   ```bash
   cd /opt/cumetria
   docker compose stop web
   ```
2. Unpack a backup over the data folder, replacing `NAME` with the backup file's date part:
   ```bash
   docker compose run --rm --no-deps --entrypoint sh \
     -v ~/cumetria-backups:/restore:ro web \
     -c 'rm -rf /data/db.sqlite3* /data/media && tar xzf /restore/cumetria-NAME.tar.gz -C /data'
   ```
3. Start the site again:
   ```bash
   docker compose start web
   ```

Only the website's own data is replaced. It lives in the `cumetria_cumetria-data` volume.

## 9. Updating later

When a pull request is merged:

```bash
cd /opt/cumetria
git pull
docker compose up -d --build
```

Database changes apply on their own when the site starts. Each update briefly restarts Cumetria and nothing else.

**To go back** to the version before:
1. Find the previous version's code with `git log --oneline -5`.
2. Run `git checkout THAT_CODE`.
3. Run `docker compose up -d --build`.

If an update changed the database, restore last night's backup too (step 8). When the fix is merged, run `git checkout main && git pull` to return.

## 10. If something goes wrong

- **Take only the website offline:** `cd /opt/cumetria && docker compose down`. The data stays in its volume; the game servers keep running.
- **See what happened:** `docker compose logs web --tail 100` and `docker compose logs caddy --tail 100`.
- **Never** delete the `cumetria_cumetria-data` volume: it is the database and the photos.
- **A game server seems affected:** stop Cumetria first (`docker compose down`), check the game server, and tell Claude what you saw.

## Before the reveal

- [ ] If you ran the fake data on the server, remove it: `docker compose exec web python manage.py seed_test_data --remove`
- [ ] Put the real group photo at `static/img/login-photo.jpg` and rebuild.
- [ ] Back up (step 8), then create the invites on the Admin page.
