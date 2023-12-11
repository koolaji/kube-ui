from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin

import subprocess
import os
import yaml
import logging

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    pass

# User credentials dictionary
user_credentials = {
    'mehrdad.kou': {'password': 'mk2mk2mk2'},
    'elham.mohamma': {'password': 'elham.mohamma_pass'},
    # Add more users as needed
}

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the provided credentials are valid
        if username in user_credentials and user_credentials[username]['password'] == password:
            user = User()
            user.id = username
            login_user(user)
            return redirect(url_for('select_page'))
        else:
            return render_template('login.html', error='Invalid username or password')

    # If the request method is GET, render the login page
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def select_page():
    return render_template('select_page.html')

# Define the list of namespaces from environment variable
allowed_namespaces_str = os.environ.get('ALLOWED_NAMESPACES', 'ngmy-dev,ngmy-uat,ngmy-qc')
allowed_namespaces = allowed_namespaces_str.split(',')
allowed_namespaces_str_curl = os.environ.get('ALLOWED_NAMESPACES', 'ngmy-dev,ngmy-uat')
allowed_namespaces_curl = allowed_namespaces_str_curl.split(',')
# Define the configuration files for each namespace from environment variable
config_files_str = os.environ.get('CONFIG_FILES', '{"ngmy-dev": "ngmy-dev.yaml", "ngmy-uat": "ngmy-uat.yaml", "ngmy-qc": "ngmy-qc.yaml"}')
config_files = yaml.safe_load(config_files_str)

def get_kubeconfig_path(namespace):
    # Map namespace to config file
    config_file = config_files.get(namespace)
    config_path = os.path.join('app/configs', config_file)

    return config_path

def run_kubectl_command(command, namespace):
    kubeconfig = get_kubeconfig_path(namespace)

    kubectl_command = [
        '/usr/local/bin/kubectl',
        '--kubeconfig', kubeconfig,
        '--namespace', namespace
    ] + command

    try:
        result = subprocess.check_output(
            kubectl_command,
            text=True, stderr=subprocess.STDOUT
        )
        logging.debug(result)
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f'Error executing kubectl command: {e.output}')
        return jsonify({'error': f'Error executing kubectl command: {e.output}'})

@app.route('/index_kube', methods=['GET', 'POST'])
def index_kube():
    if request.method == 'POST':
        selected_option = request.form.get('selection')

        if selected_option == 'kube_log':
            return render_template('index_kube.html')
        elif selected_option == 'curl':
            return render_template('index_curl.html')

    return redirect(url_for('select_page'))

@app.route('/namespaces', methods=['GET'])
def get_namespaces():
    return jsonify({'namespaces': allowed_namespaces})

@app.route('/namespaces_curl', methods=['GET'])
def get_namespaces_curl():
    return jsonify({'namespaces': allowed_namespaces_curl})

@app.route('/pods', methods=['POST'])
def get_pods():
    namespace = request.form.get('namespace', 'ngmy-dev')
    try:
        result = run_kubectl_command(['get', 'pods', '--output=jsonpath="{.items[*].metadata.name}"'], namespace)
        # Split the result and remove double quotes
        pods_data = result.replace('"', '').split()

        return jsonify({'pods': pods_data})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/logs', methods=['POST'])
def get_logs():
    namespace = request.form.get('namespace', 'ngmy-dev')
    pod_name = request.form.get('pod_name')
    try:
        response = run_kubectl_command(['logs', pod_name], namespace)
        # Extract the content from the response object
        logs = response

        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/curl', methods=['POST'])
def execute_curl():
    namespace = request.form.get('namespace', 'ngmy-dev')
    pod_name = request.form.get('pod_name')
    curl_command = request.form.get('curl_command')

    try:
        response = run_kubectl_command(['exec', '-it', pod_name, '--', 'sh', '-c', curl_command], namespace)
        # Assuming run_kubectl_command returns a Flask Response object
        curl_output = response
        return render_template('result.html', curl_output=curl_output)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
