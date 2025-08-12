# SSH connection info: ssh merk@100.121.231.16
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World! This is the Raspberry Pi webserver for the CST_590_Computer_Science_Capstone_Project.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
