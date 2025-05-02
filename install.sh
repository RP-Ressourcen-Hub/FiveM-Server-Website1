#!/bin/bash

# Installationsskript für die FiveM Server Webseite
# Dieses Skript sollte mit Root-Rechten ausgeführt werden

echo "FiveM Server Webseite - Installation"
echo "===================================="
echo ""

# Systemaktualisierung
echo "1. Systemaktualisierung..."
apt update
apt upgrade -y

# Installation der benötigten Software
echo "2. Installation der benötigten Software..."
apt install -y python3 python3-pip python3-venv postgresql nginx curl git certbot python3-certbot-nginx ufw

# PostgreSQL-Datenbank einrichten
echo "3. PostgreSQL-Datenbank einrichten..."
systemctl start postgresql
systemctl enable postgresql

# Benutzer und Datenbank anlegen
read -p "Datenbankbenutzer erstellen [fivem_user]: " db_user
db_user=${db_user:-fivem_user}

read -sp "Datenbankpasswort eingeben: " db_password
echo ""
read -sp "Datenbankpasswort bestätigen: " db_password_confirm
echo ""

if [ "$db_password" != "$db_password_confirm" ]; then
    echo "Fehler: Die Passwörter stimmen nicht überein!"
    exit 1
fi

read -p "Datenbankname erstellen [fivem_db]: " db_name
db_name=${db_name:-fivem_db}

sudo -u postgres psql -c "CREATE USER $db_user WITH PASSWORD '$db_password';"
sudo -u postgres psql -c "CREATE DATABASE $db_name OWNER $db_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;"

# Webverzeichnis erstellen
echo "4. Webverzeichnis erstellen..."
mkdir -p /var/www/fivem-website

# Aktuelle Verzeichnis nach /var/www/fivem-website kopieren
echo "5. Projektdateien kopieren..."
cp -r ./* /var/www/fivem-website/
chown -R www-data:www-data /var/www/fivem-website
chmod -R 755 /var/www/fivem-website

# Python-Umgebung einrichten
echo "6. Python-Umgebung einrichten..."
cd /var/www/fivem-website
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install flask==2.3.3 flask-sqlalchemy==3.1.1 flask-migrate==4.0.5 flask-login==0.6.3 flask-wtf==1.2.1 email-validator==2.1.0 flask-bcrypt==1.0.1 sendgrid==6.10.0 itsdangerous==2.1.2 gunicorn==21.2.0 psycopg2-binary==2.9.9 pytz==2023.3 python-dotenv==1.0.0 watchdog==3.0.0

# Umgebungsvariablen konfigurieren
echo "7. Umgebungsvariablen konfigurieren..."
read -p "Domain-Name eingeben (z.B. meinserver.de): " domain
read -p "SendGrid API-Key eingeben (leer lassen falls nicht vorhanden): " sendgrid_api_key
read -p "E-Mail für Absender (z.B. noreply@meinserver.de): " mail_sender
read -sp "Geheimschlüssel für die Anwendung (min. 16 Zeichen): " secret_key
echo ""

cat > /var/www/fivem-website/.env << EOF
DATABASE_URL=postgresql://$db_user:$db_password@localhost/$db_name
SECRET_KEY=$secret_key
SENDGRID_API_KEY=$sendgrid_api_key
MAIL_DEFAULT_SENDER=$mail_sender
BASE_URL=https://$domain
EOF

chown www-data:www-data /var/www/fivem-website/.env
chmod 600 /var/www/fivem-website/.env

# Gunicorn-Konfiguration
echo "8. Gunicorn konfigurieren..."
cat > /var/www/fivem-website/gunicorn_config.py << EOF
bind = "127.0.0.1:8000"
workers = 3
timeout = 120
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
loglevel = "info"
EOF

mkdir -p /var/log/gunicorn
chown -R www-data:www-data /var/log/gunicorn

# Nginx-Konfiguration
echo "9. Nginx konfigurieren..."
cat > /etc/nginx/sites-available/fivem-website << EOF
server {
    listen 80;
    server_name $domain www.$domain;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/fivem-website/static;
        expires 30d;
    }

    client_max_body_size 5M;
}
EOF

ln -sf /etc/nginx/sites-available/fivem-website /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Systemdienst erstellen
echo "10. Systemdienst erstellen..."
cat > /etc/systemd/system/fivem-website.service << EOF
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
EOF

systemctl daemon-reload
systemctl start fivem-website
systemctl enable fivem-website

# Datenbank-Migration
echo "11. Datenbank-Migration ausführen..."
cd /var/www/fivem-website
sudo -u www-data venv/bin/flask db upgrade

# SSL-Zertifikat einrichten
echo "12. SSL-Zertifikat einrichten..."
read -p "Möchtest du ein SSL-Zertifikat einrichten? (j/n): " setup_ssl
if [ "$setup_ssl" = "j" ] || [ "$setup_ssl" = "J" ]; then
    certbot --nginx -d $domain -d www.$domain
else
    echo "SSL-Zertifikat wird übersprungen. Die Website ist nur über HTTP erreichbar."
fi

# Firewall konfigurieren
echo "13. Firewall konfigurieren..."
ufw allow ssh
ufw allow http
ufw allow https
read -p "Firewall aktivieren? (j/n): " enable_ufw
if [ "$enable_ufw" = "j" ] || [ "$enable_ufw" = "J" ]; then
    ufw enable
else
    echo "Firewall wird nicht aktiviert."
fi

echo ""
echo "Die Installation ist abgeschlossen!"
echo "Deine Webseite ist jetzt unter http://$domain erreichbar."
if [ "$setup_ssl" = "j" ] || [ "$setup_ssl" = "J" ]; then
    echo "Die Webseite ist auch über https://$domain erreichbar."
fi
echo ""
echo "Datenbank-Details:"
echo "- Benutzer: $db_user"
echo "- Datenbank: $db_name"
echo ""
echo "Bei Problemen überprüfe die Logs mit folgenden Befehlen:"
echo "sudo tail -f /var/log/gunicorn/error.log"
echo "sudo tail -f /var/log/nginx/error.log"
echo "sudo journalctl -u fivem-website"