from flask import Flask, request
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
	return "You're not supposed to be here :3"

@app.route('/webhook', methods=['POST'])
def webhook():
	if request.method == 'POST':
		repo_dir = os.path.dirname(os.path.realpath(__file__))
		os.chdir(repo_dir)
		subprocess.run(['git', 'pull'])
		subprocess.run(['pm2', 'restart', 'locomotion'])
		return 'Success', 200
	else:
		return 'Invalid Method', 400

if __name__ == "__main__":
	app.run(port=5000)