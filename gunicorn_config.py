# gunicorn_config.py

# Set the host and port
bind = "127.0.0.1:5000"

# Specify the number of workers
workers = 4

# Set the working directory to your Flask app
chdir = "app"

# Specify the module and app name
module = "app.kube_log:app"

