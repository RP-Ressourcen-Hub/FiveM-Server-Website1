# FiveM Server Webseite - Installationsanleitung

Diese Anleitung beschreibt die Installation und Konfiguration der FiveM Server Webseite auf einem Debian 12 VServer.

## Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [Systemaktualisierung](#systemaktualisierung)
3. [Installation der benötigten Software](#installation-der-benötigten-software)
4. [PostgreSQL-Datenbank einrichten](#postgresql-datenbank-einrichten)
5. [Projektdateien hochladen](#projektdateien-hochladen)
6. [Python-Umgebung einrichten](#python-umgebung-einrichten)
7. [Umgebungsvariablen konfigurieren](#umgebungsvariablen-konfigurieren)
8. [Datenbank-Migration ausführen](#datenbank-migration-ausführen)
9. [Gunicorn und Nginx konfigurieren](#gunicorn-und-nginx-konfigurieren)
10. [Systemdienst erstellen](#systemdienst-erstellen)
11. [SSL-Zertifikat einrichten (Let's Encrypt)](#ssl-zertifikat-einrichten)
12. [Firewall konfigurieren](#firewall-konfigurieren)
13. [Testen der Installation](#testen-der-installation)
14. [Problembehandlung](#problembehandlung)

## Voraussetzungen

- Debian 12 VServer (mindestens 1 GB RAM, 1 vCPU)
- Root-Zugriff oder Benutzer mit sudo-Rechten
- Eine Domain, die auf die IP-Adresse des VServers zeigt

## Systemaktualisierung

Führe zunächst eine Systemaktualisierung durch:

```bash
sudo apt update
sudo apt upgrade -y
```

## Installation der benötigten Software

Installiere alle erforderlichen Pakete:

```bash
sudo apt install -y python3 python3-pip python3-venv postgresql nginx curl git
```

## PostgreSQL-Datenbank einrichten

1. Starte den PostgreSQL-Dienst:

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. Erstelle einen Datenbankbenutzer und eine Datenbank:

```bash
sudo -u postgres psql -c "CREATE USER fivem_user WITH PASSWORD 'DeinSicheresPasswort';"
sudo -u postgres psql -c "CREATE DATABASE fivem_db OWNER fivem_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fivem_db TO fivem_user;"
```

Ersetze 'DeinSicheresPasswort' durch ein sicheres Passwort.

## Projektdateien hochladen

1. Erstelle ein Verzeichnis für die Anwendung:

```bash
sudo mkdir -p /var/www/fivem-website
```

2. Lade die ZIP-Datei auf deinen Server hoch (z.B. mit SCP oder SFTP)

3. Entpacke die ZIP-Datei:

```bash
sudo unzip fivem-website.zip -d /var/www/fivem-website
sudo chown -R www-data:www-data /var/www/fivem-website
```

## Python-Umgebung einrichten

1. Erstelle eine virtuelle Python-Umgebung:

```bash
cd /var/www/fivem-website
sudo -u www-data python3 -m venv venv
```

2. Installiere die benötigten Pakete:

```bash
sudo -u www-data venv/bin/pip install -r requirements.txt
sudo -u www-data venv/bin/pip install gunicorn psycopg2-binary
```

## Umgebungsvariablen konfigurieren

Erstelle eine `.env` Datei für Umgebungsvariablen:

```bash
sudo nano /var/www/fivem-website/.env
```

Füge folgende Zeilen hinzu:

```
DATABASE_URL=postgresql://fivem_user:DeinSicheresPasswort@localhost/fivem_db
SECRET_KEY=dein-sehr-geheimer-schluessel
SENDGRID_API_KEY=dein-sendgrid-api-key
MAIL_DEFAULT_SENDER=noreply@deinewebsite.de
BASE_URL=https://deinewebsite.de
```

Ersetze die Werte mit deinen eigenen Daten.

## Datenbank-Migration ausführen

```bash
cd /var/www/fivem-website
sudo -u www-data venv/bin/flask db upgrade
```

## Gunicorn und Nginx konfigurieren

### Gunicorn-Konfiguration

Erstelle eine Gunicorn-Konfigurationsdatei:

```bash
sudo nano /var/www/fivem-website/gunicorn_config.py
```

Füge folgenden Inhalt ein:

```python
bind = "127.0.0.1:8000"
workers = 3
timeout = 120
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
loglevel = "info"
```

Erstelle Log-Verzeichnis:

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown -R www-data:www-data /var/log/gunicorn
```

### Nginx-Konfiguration

Erstelle eine Nginx-Server-Konfiguration:

```bash
sudo nano /etc/nginx/sites-available/fivem-website
```

Füge folgenden Inhalt ein:

```nginx
server {
    listen 80;
    server_name deinewebsite.de www.deinewebsite.de;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/fivem-website/static;
        expires 30d;
    }

    client_max_body_size 5M;
}
```

Ersetze `deinewebsite.de` mit deiner eigenen Domain.

Aktiviere die Konfiguration:

```bash
sudo ln -s /etc/nginx/sites-available/fivem-website /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Optional, entfernt die Standardkonfiguration
sudo nginx -t  # Teste die Nginx-Konfiguration
sudo systemctl restart nginx
```

## Systemdienst erstellen

Erstelle einen Systemdienst für Gunicorn:

```bash
sudo nano /etc/systemd/system/fivem-website.service
```

Füge folgenden Inhalt ein:

```
[Unit]
Description=FiveM Website Gunicorn Service
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/fivem-website
Environment="PATH=/var/www/fivem-website/venv/bin"
EnvironmentFile=/var/www/fivem-website/.env
ExecStart=/var/www/fivem-website/venv/bin/gunicorn -c gunicorn_config.py main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Starte den Dienst:

```bash
sudo systemctl daemon-reload
sudo systemctl start fivem-website
sudo systemctl enable fivem-website
```

## SSL-Zertifikat einrichten

Installiere Certbot für Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

Richte das SSL-Zertifikat ein:

```bash
sudo certbot --nginx -d deinewebsite.de -d www.deinewebsite.de
```

Folge den Anweisungen auf dem Bildschirm. Certbot wird deine Nginx-Konfiguration automatisch aktualisieren.

## Firewall konfigurieren

Wenn du UFW als Firewall verwendest:

```bash
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

## Testen der Installation

Besuche deine Website mit einem Webbrowser, um zu überprüfen, ob alles funktioniert.

## Problembehandlung

### Überprüfen der Logs

Wenn Probleme auftreten, prüfe die Logs:

```bash
# Gunicorn-Logs
sudo tail -f /var/log/gunicorn/error.log

# Nginx-Logs
sudo tail -f /var/log/nginx/error.log

# Systemd-Logs
sudo journalctl -u fivem-website
```

### Berechtigungsprobleme

Wenn Berechtigungsprobleme auftreten:

```bash
sudo chown -R www-data:www-data /var/www/fivem-website
sudo chmod -R 755 /var/www/fivem-website
```

### Datenbank-Probleme

Um die Datenbankverbindung zu überprüfen:

```bash
sudo -u www-data psql -U fivem_user -h localhost -d fivem_db
```

### Neustart aller Dienste

Bei Problemen versuche, alle Dienste neu zu starten:

```bash
sudo systemctl restart postgresql
sudo systemctl restart fivem-website
sudo systemctl restart nginx
```

## Aktualisierung der Website

Um die Website zu aktualisieren:

1. Lade die neue ZIP-Datei hoch
2. Entpacke sie und ersetze die alten Dateien
3. Führe die Datenbank-Migration aus (falls nötig)
4. Starte den Dienst neu:

```bash
sudo systemctl restart fivem-website
```

---

Bei Fragen oder Problemen wende dich an den Support.