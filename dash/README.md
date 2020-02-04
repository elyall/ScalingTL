# [How to install nginx on ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04)

Install nginx
```
sudo apt update
sudo apt install nginx
systemctl status nginx # check status
systemctl start nginx # start if not already running
```

Update firewall
```
sudo ufw allow 'OpenSSH'
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'
sudo ufw enable
```

Create directories
```
sudo mkdir -p /var/www/dataidealist.xyz/html
sudo chown -R $USER:$USER /var/www/dataidealist.xyz/html
sudo chmod -R 755 /var/www/dataidealist.xyz
```

Update nginx to host website
```
nano /var/www/dataidealist.xyz/html/index.html
```
```HTML
<html>
    <head>
        <title>Welcome to dataidealist.xyz!</title>
    </head>
    <body>
        <h1>Success!  The dataidealist.xyz server block is working!</h1>
    </body>
</html>
```
```
sudo nano /etc/nginx/sites-available/dataidealist.xyz
```
```
server {
        listen 80;
        listen [::]:80;

        root /var/www/example.com/html;
        index index.html index.htm index.nginx-debian.html;

        server_name dataidealist.xyz www.dataidealist.xyz;

        location / {
                try_files $uri $uri/ =404;
        }
}
```
```
sudo ln -s /etc/nginx/sites-available/dataidealist.xyz /etc/nginx/sites-enabled/
sudo nano /etc/nginx/nginx.conf # uncomment `server_names_hash_bucket_size 64`
sudo nginx -t
sudo systemctl restart nginx
```

SET UP "A RECORDS" AT DOMAIN HOST (i.e. NameCheap)

Type | Host | Value | TTL
--- | --- | --- | ---
A | @   | XXX.XXX.XXX.XXX | Automatic
A | www | XXX.XXX.XXX.XXX | Automatic  

# [How to serve app with gunicorn](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04)

Install gunicorn
```
pip install wheel gunicorn flask
```

Create website and wsgi socket
```
mkdir website
cd website
nano ~/website/website.py
```
```python
import dash
import dash_core_components as dcc
import dash_html_components as html

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0',debug=True)
```
```
nano ~/website/wsgi.py
```
```python
from website import server

if __name__ == "__main__":
    server.run()
```

Set up gunicorn
```
gunicorn --bind 0.0.0.0:8050 wsgi:server
sudo nano /etc/systemd/system/website.service
```
```
[Unit]
Description=Gunicorn instance to serve website
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/website
Environment="PATH=/home/ubuntu/.local/bin"
ExecStart=/home/ubuntu/.local/bin/gunicorn --workers 3 --bind unix:website.sock -m 007 wsgi:server

[Install]
WantedBy=multi-user.target
```
```
sudo systemctl start website
sudo systemctl enable website
```

Update nginx and firewall
```
sudo nano /etc/nginx/sites-available/dataidealist.xyz # change location info
```
```
server {
        root /var/www/dataidealist.xyz/html;
        index index.html index.htm index.nginx-debian.html;

        server_name dataidealist.xyz www.dataidealist.xyz;

        location / {
                include proxy_params;
                proxy_pass http://unix:/home/ubuntu/website/website.sock;
        }
}
```
```
sudo nginx -t # check if everything is okay
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'
```

Set up HTTPS certificate
```
sudo add-apt-repository ppa:certbot/certbot
sudo apt-get update
sudo apt install python-certbot-nginx
sudo certbot --nginx -d dataidealist.xyz -d www.dataidealist.xyz
sudo ufw delete allow 'Nginx HTTP'
```

# Update website
Change website by altering `~/website/website.py` then run:
```
sudo systemctl restart website
```