from fire import Fire
import os, time, json, chess, string, random, hashlib, sqlite3, requests
from flask import Flask, request, abort, render_template, redirect, current_app, session
from typing import List

class DBWraper:
	def __init__(self, path: str):
		self.path = path
		self.connection = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
		self.connection.row_factory = sqlite3.Row
		self.cursor = self.connection.cursor()

		self.cursor.execute('''CREATE TABLE IF NOT EXISTS User (
			id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
			name TEXT UNIQUE,
			pw TEXT,
			salt TEXT,
			sign_in_time UNSIGNED INTEGER,
			recent_login_time UNSIGNED INTEGER
		)''')

		self.cursor.execute('''CREATE TABLE IF NOT EXISTS History (
			id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
			black INTEGER,
			white INTEGER,
			history TEXT,
			timestamp UNSIGNED INTEGER,
			FOREIGN KEY(black) REFERENCES User(id),
			FOREIGN KEY(white) REFERENCES User(id)
		)''')

		query = "INSERT INTO User(name) VALUES (?)"
		try:
			self.cursor.execute(query, ('easy',))
			self.cursor.execute(query, ('hard',))
		except:
			pass

	def is_user_exist(self, name: str) -> bool:
		query = "SELECT * FROM User WHERE name=?"
		self.cursor.execute(query, (name,))
		return len(self.cursor.fetchall()) > 0

	def get_uid(self, name: str, pw: str, ignore_pw=False) -> int:
		query = "SELECT * FROM User WHERE name=?"
		self.cursor.execute(query, (name,))
		row = self.cursor.fetchone()
		if row is None:
			return -1
		if ignore_pw or hashlib.sha256((row['salt']+pw).encode()).hexdigest() == row['pw']:
			query = "UPDATE User SET recent_login_time=? WHERE id=?"
			self.cursor.execute(query, (int(time.time()), row['id']))
			return row['id']
		else:
			return -1

	def add_user(self, name: str, pw: str) -> bool:
		query = "INSERT INTO User(name, pw, salt, sign_in_time, recent_login_time) VALUES (?, ?, ?, ?, ?)"
		chars = string.ascii_letters + string.digits
		salt = ''.join([random.choice(chars) for _ in range(16)])
		pw = hashlib.sha256((salt+pw).encode()).hexdigest()
		try:
			self.cursor.execute(query, (name, pw, salt, int(time.time()), int(time.time())))
		except:
			return False
		return True

	def get_histories(self, uid: int, start: int, to: int) -> List[str]:
		query = "SELECT * FROM History WHERE black=? OR white=? ORDER BY id DESC LIMIT ?, ?"
		self.cursor.execute(query, (uid, uid, start, to))
		rows = self.cursor.fetchall()
		return [{'history': row['history'], 'color': 'black' if row['black'] == uid else 'white'} for row in rows]

	def add_history(self, black: int, white: int, history: str) -> bool:
		query = "INSERT INTO History(black, white, history, timestamp) VALUES (?, ?, ?, ?)"
		try:
			self.cursor.execute(query, (black, white, history, int(time.time())))
		except:
			return False
		return True

class AIAPIWraper:
	def __init__(self, host, port):
		self.url = 'http://{}:{}'.format(host, port)

	def predict(self, mode: str, fen: str) -> string:
		url = self.url + '/' + mode
		response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps({'fen':fen}))
		if response.status_code != 200:
			return None
		resp = json.loads(response.text)
		return resp

app = Flask(__name__)
chars = string.ascii_letters + string.digits
app.secret_key = ''.join([random.choice(chars) for _ in range(16)])

#############
# TEST ONLY #
#############
@app.route('/uid', methods=['GET'])
def uid():
	return str(session.get('uid', -1))

@app.route('/', methods=['GET'])
def root():
	return redirect('/index')

@app.route('/index', methods=['GET'])
def index():
	return render_template('index.html')

@app.route('/play', methods=['GET'])
def play():
	return render_template('play.html')

@app.route('/history', methods=['GET'])
def history():
	return render_template('history.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
	session.pop('uid', None)
	return redirect('index')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')

	name = request.form['name']
	pw = request.form['pw']

	uid = current_app.db.get_uid(name, pw)

	if uid != -1:
		session['uid'] = uid
	return redirect('index')

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'GET':
		return render_template('register.html')

	name = request.form['name']
	pw = request.form['pw']

	current_app.db.add_user(name, pw)
	return redirect('login')

@app.route('/check_user', methods=['POST'])
def check_user():
	name = request.form['name']

	if current_app.db.is_user_exist(name):
		return {'message': 'user is exist'}
	else:
		return {'message': 'user is not exist'}

###########################
# GET METHOD IS TEST ONLY #
###########################
@app.route('/predict', methods=['GET', 'POST'])
def predict():
	if request.method == 'GET':
		return render_template('predict.html')

	mode = request.form['mode']
	fen = request.form['fen']

	action = current_app.ai.predict(mode, fen)
	if action is None:
		return abort(400, 'worng mode or fen')
	return action

@app.route('/get_histories', methods=['POST'])
def get_histories():
	page = request.form['page']

	limit_start = 10 * (page-1)
	limit_end = 10 * page

	if session.uid is None:
		return {'message': 'login first'}

	return {
		'message': 'success',
		'result': current_app.db.get_histories(session.uid, limit_start, limit_end)
	}

@app.route('/add_history', methods=['POST'])
def add_history():
	mode = request.form['mode']
	player_color = request.form['player_color']
	history = request.form['history']

	if session.uid is None:
		return {'message': 'login first'}

	if player_color not in ['black', 'white']:
		return {'message': 'wrong color'}

	ai_uid = current_app.db.get_uid(mode, pw='', ignore_pw=True)
	if player_color == 'black':
		black = session.uid
		id
	else:
		black = ai_uid
		white = session.uid

	current_app.db.add_history(black, white, history)
	return {'message': 'success'}

def main(ai_api_url: str, ai_api_port: int, web_server_port: int):
	app.db = DBWraper('db.db')
	app.ai = AIAPIWraper(ai_api_url, ai_api_port)
	app.run(host='0.0.0.0', port=web_server_port)

if __name__ == '__main__':
	Fire(main)
