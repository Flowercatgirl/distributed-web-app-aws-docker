import os
from flask import Flask, request, render_template_string
import paramiko
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

EC2_IP = os.environ.get("EC2_IP", "your-ec2-ip-here")
EC2_USER = "ubuntu"
EC2_KEY_PATH = os.environ.get("EC2_KEY_PATH", "/path/to/your-key.pem")
EC2_SCRIPT_PATH = "/home/ubuntu/wiki.py"

DB_CONFIG = {
    'host': 'localhost',
    'port': 7888,
    'user': 'appuser',
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': 'search_cache'
}

HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Wikipedia Search Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
        input { padding: 10px; width: 300px; margin: 10px; }
        button { padding: 10px 20px; background: blue; color: white; border: none; cursor: pointer; }
        .result { margin-top: 20px; padding: 20px; border-radius: 5px; }
        .cached { background: #e8f5e9; border-left: 5px solid green; }
        .live { background: #e3f2fd; border-left: 5px solid blue; }
        .badge { font-size: 12px; display: inline-block; padding: 2px 8px; border-radius: 10px; margin-bottom: 10px; }
        .cached-badge { background: green; color: white; }
        .live-badge { background: blue; color: white; }
    </style>
</head>
<body>
    <h1>Wikipedia Search Assistant</h1>
    <form method="POST">
        <input type="text" name="query" placeholder="Search..." required>
        <button type="submit">Search</button>
    </form>
    {% if result %}
    <div class="result {% if cached %}cached{% else %}live{% endif %}">
        {% if cached %}
        <div class="badge cached-badge">Cached Result</div>
        {% else %}
        <div class="badge live-badge">Live Result</div>
        {% endif %}
        {{ result }}
    </div>
    <a href="/">Search again</a>
    {% endif %}
</body>
</html>
"""

def get_cached_result(query):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT result FROM cache WHERE query = %s", (query,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Error as e:
        print(f"DB error: {e}")
        return None

def save_to_cache(query, result):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cache (query, result) VALUES (%s, %s) ON DUPLICATE KEY UPDATE result = %s",
            (query, result, result)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"Save error: {e}")
        return False

def search_on_ec2(query):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=EC2_IP, username=EC2_USER, key_filename=EC2_KEY_PATH, timeout=30)
        command = f"python3 {EC2_SCRIPT_PATH} '{query}'"
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        ssh.close()
        if exit_status != 0 or error:
            return None, f"Error: {error}"
        return output, None
    except Exception as e:
        return None, f"Connection error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        query = request.form['query']
        if not query.strip():
            return render_template_string(HOME_PAGE, error="Please enter a search term.")
        
        cached_result = get_cached_result(query)
        if cached_result:
            return render_template_string(HOME_PAGE, result=cached_result, cached=True)
        
        result, error = search_on_ec2(query)
        if error:
            return render_template_string(HOME_PAGE, error=error)
        
        save_to_cache(query, result)
        return render_template_string(HOME_PAGE, result=result, cached=False)
    
    return render_template_string(HOME_PAGE, result=None)

if __name__ == '__main__':
    print("Flask with MySQL Cache running on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
