from fire import Fire
import os, time, json, chess, string, random, hashlib, sqlite3, requests
from flask import Flask, request, abort, render_template, redirect, current_app, session
from typing import List, Dict, Union, Optional
from threading import Lock

from logging.config import dictConfig

dictConfig({
	'version': 1,
	'formatters': { 'default': {
		'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
	}},
	'handlers': {
		'wsgi': {
			'class': 'logging.StreamHandler',
			'stream': 'ext://flask.logging.wsgi_errors_stream',
			'formatter': 'default'
		},
		'local_file': {
			'class': 'logging.FileHandler',
			'filename': 'log.txt'
		}
	},
	'root': {
		'level': 'INFO',
		'handlers': ['wsgi', 'local_file']
	}
})

class DBWraper:
	def __init__(self, path: str):
		self.path = path
		self.connection = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
		self.connection.row_factory = sqlite3.Row
		self.cursor = self.connection.cursor()
		self.lock = Lock()

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
		with self.lock:
			self.cursor.execute(query, (name,))
		return len(self.cursor.fetchall()) > 0

	def get_uid(self, name: str, pw: str, ignore_pw=False) -> int:
		query = "SELECT * FROM User WHERE name=?"
		with self.lock:
			self.cursor.execute(query, (name,))
			row = self.cursor.fetchone()
		if row is None:
			return -1
		if ignore_pw or hashlib.sha256((row['salt']+pw).encode()).hexdigest() == row['pw']:
			query = "UPDATE User SET recent_login_time=? WHERE id=?"
			with self.lock:
				self.cursor.execute(query, (int(time.time()), row['id']))
			return row['id']
		else:
			return -1

	def get_user_name(self, uid: int) -> Optional[str]:
		query = "SELECT * FROM User WHERE id=?"
		with self.lock:
			self.cursor.execute(query, (uid,))
			row = self.cursor.fetchone()
		if row is None:
			return None
		return row['name']

	def add_user(self, name: str, pw: str) -> bool:
		query = "INSERT INTO User(name, pw, salt, sign_in_time, recent_login_time) VALUES (?, ?, ?, ?, ?)"
		chars = string.ascii_letters + string.digits
		salt = ''.join([random.choice(chars) for _ in range(16)])
		pw = hashlib.sha256((salt+pw).encode()).hexdigest()
		try:
			with self.lock:
				self.cursor.execute(query, (name, pw, salt, int(time.time()), int(time.time())))
		except:
			return False
		return True

	def get_history(self, history_id: int) -> Optional[str]:
		query = "SELECT * FROM History WHERE id=?"
		with self.lock:
			self.cursor.execute(query, (history_id,))
			row = self.cursor.fetchone()
		if row is None:
			return None
		return row['history']

	def get_histories(self, uid: int, start: int, to: int) -> List[Dict[str, Union[int, str]]]:
		query = "SELECT * FROM History WHERE black=? OR white=? ORDER BY id DESC LIMIT ?, ?"
		with self.lock:
			self.cursor.execute(query, (uid, uid, start, to))
			rows = self.cursor.fetchall()

		histories = []
		for row in rows:
			history = {}
			history['id'] = row['id']
			history['color'] = 'black' if row['black'] == uid else 'white'
			history['enemy'] = row['white'] if row['black'] == uid else row['black']
			history['enemy'] = self.get_user_name(history['enemy'])
			histories.append(history)

		return histories

	def num_histories(self, uid: int) -> int:
		query = "SELECT COUNT(*) from History WHERE black=? OR white=?"
		with self.lock:
			self.cursor.execute(query, (uid, uid))
			row = self.cursor.fetchone()
		return row["COUNT(*)"]

	def add_history(self, black: int, white: int, history: str) -> bool:
		query = "INSERT INTO History(black, white, history, timestamp) VALUES (?, ?, ?, ?)"
		try:
			with self.lock:
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

def get_message():
	message = ''

	session_message = session.pop('message', None)
	if session_message is not None:
		message = session_message

	return message

@app.route('/', methods=['GET'])
def root():
	return redirect('/index')

@app.route('/index', methods=['GET'])
def index():
	if session.get('uid', -1) == -1:
		return render_template('index.html', message=get_message())
	else:
		return redirect('/home')

@app.route('/play', methods=['GET'])
def play():
	return render_template('play.html', view=random.choice(['black', 'white']), uid=session.get('uid', -1))

@app.route('/home', methods=['GET'])
def home():
	uid = session.get('uid', -1)
	if uid == -1:
		session['message'] = 'login first'
		return redirect('/index')

	name = current_app.db.get_user_name(uid)

	num_page = (current_app.db.num_histories(uid) -1) // 10 + 1
	num_page = max(1, num_page)

	page = request.args.get('page', 1)
	page = min(max(1, page), num_page)

	limit_start = 10 * (page-1)
	limit_end = 10 * page
	histories = current_app.db.get_histories(uid, limit_start, limit_end)

	return render_template(
		'home.html',
		name=name,
		histories=histories,
		page=page,
		num_page=num_page
	)

@app.route('/history', methods=['GET'])
def history():
	history_id = request.args.get('id')
	view = request.args.get('view', 'white')

	history = current_app.db.get_history(history_id)
	if history == None:
		return abort(404, "no such history")
	history = history.split(',')

	return render_template('history.html', history=history, view=view)

@app.route('/logout', methods=['GET'])
def logout():
	session.pop('uid', None)
	session.pop('name', None)
	return redirect('/index')

@app.route('/signup', methods=['POST'])
def signup():
	name = request.form['name']
	pw = request.form['pw']

	if current_app.db.add_user(name, pw):
		uid = current_app.db.get_uid(name, pw)
		session['uid'] = uid
		session['name'] = name
	else:
		session['message'] = 'failed to register'

	return redirect('/index')

@app.route('/login', methods=['POST'])
def login():
	name = request.form['name']
	pw = request.form['pw']

	uid = current_app.db.get_uid(name, pw)

	if uid != -1:
		session['uid'] = uid
		session['name'] = name
	else:
		session['message'] = 'login failed'

	return redirect('/index')

@app.route('/predict', methods=['POST'])
def predict():
	mode = request.form['mode']
	fen = request.form['fen']

	action = current_app.ai.predict(mode, fen)
	if action is None:
		return abort(400, 'worng mode or fen')
	return action

@app.route('/add-history', methods=['POST'])
def add_history():
	mode = request.form['mode']
	player_color = request.form['player-color']
	history = request.form['history']

	if session.get('uid', -1) == -1:
		return abort(400, 'login first')

	if player_color not in ['black', 'white']:
		return abort(400, 'wrong color')

	ai_uid = current_app.db.get_uid(mode, pw='', ignore_pw=True)
	if player_color == 'black':
		black = session['uid']
		white = ai_uid
	else:
		black = ai_uid
		white = session['uid']

	history_list = history.split(',')

	try:
		board = chess.Board()
		for action in history_list:
			board.push_uci(action)
		is_valid = board.outcome() is not None
	except:
		is_valid = False

	if not is_valid:
		return abort(400, 'wrong history')

	if current_app.db.add_history(black, white, history):
		return 'success'
	else:
		return abort(500, 'failed')

def main(ai_api_url: str, ai_api_port: int, web_server_port=12345):
	app.db = DBWraper('db.db')
	app.ai = AIAPIWraper(ai_api_url, ai_api_port)
	app.run(host='0.0.0.0', port=web_server_port)

if __name__ == '__main__':
	Fire(main)
