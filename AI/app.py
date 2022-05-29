import chess
import random
import sqlite3
import numpy as np
from fire import Fire
from flask import Flask, request, abort, current_app
from flask_restx import Api, Resource

import ctypes
from multiprocessing import Process, Value, Manager
from threading import Lock

from chess_zero.agent.player_chess import ChessPlayer
from chess_zero.agent.player_chess import GentleChessPlayer
from chess_zero.config import Config, PlayWithHumanConfig
from chess_zero.env.chess_env import ChessEnv
from chess_zero.agent.model_chess import ChessModel
from chess_zero.lib.model_helper import load_best_model_weight
from chess_zero.lib.logger import setup_logger

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

MODES = ['easy', 'hard']

config = Config(config_type='normal')
config.resource.create_directories()
setup_logger(config.resource.main_log_path)
hc = PlayWithHumanConfig()
hc.tau_decay_rate = 0.99 # maintain probabilitic prediction
hc.update_play_config(config.play)

app = Flask(__name__)
api = Api(app)

def get_action(player, env, ret):
	res = player.action(env, return_all=True)
	ret['action'], ret['probabilities'], ret['confidence'] = res

def clear_white_space(fen):
	new_fen = fen
	fen = ''

	while fen != new_fen:
		fen = new_fen
		new_fen = fen.replace('  ', ' ')

	if fen[0] == ' ':
		fen = fen[1:]
	if fen[-1] == ' ':
		fen = fen[:-1]

	return fen

def get_cache(cursor, mode, fen):
	query = "SELECT * FROM Cache WHERE mode=? AND fen=?"
	cursor.execute(query, (mode, fen))
	row = cursor.fetchone()

	if row is None:
		return None

	query = "SELECT * FROM ActionProbs WHERE cacheid=?"
	cursor.execute(query, (row['id'],))
	rows = cursor.fetchall()

	confidence = {}
	probabilities = np.zeros(config.n_labels)
	for row in rows:
		probabilities[row['action']] = row['probability']
		confidence[row['action']] = row['confidence']
	probabilities /= np.sum(probabilities)

	action = np.random.choice(range(config.n_labels), p=probabilities)
	return {'action': config.labels[action], 'confidence': confidence[action]}

def put_cache(cursor, mode, fen, probabilities, confidence):
	query = "INSERT INTO Cache(mode, fen) VALUES (?, ?)"
	try:
		cursor.execute(query, (mode, fen))
	except:
		return

	query = "SELECT * FROM Cache WHERE mode=? AND fen=?"
	try:
		cursor.execute(query, (mode, fen))
		cacheid = cursor.fetchone()['id']
	except:
		return

	query = "INSERT INTO ActionProbs(cacheid, action, probability, confidence) VALUES (?, ?, ?, ?)"
	for action, (probability, conf) in enumerate(zip(probabilities, confidence)):
		if probability != 0:
			try:
				cursor.execute(query, (cacheid, action, probability, conf))
			except:
				pass

@api.route('/<string:mode>')
class AI_REST_API(Resource):
	def post(self, mode):
		# get request
		req = request.json

		pipe_lock = current_app.pipe_lock
		reserved_pipe_pools = current_app.reserved_pipe_pools
		model_lock = current_app.model_lock
		model = current_app.model
		db_lock = current_app.db_lock

		# check request
		if not mode in MODES:
			return abort(400, 'wrong mode')
		if 'fen' not in req:
			return abort(400, 'there is no fen in the request')
		fen = clear_white_space(req['fen'])

		# create env
		try:
			env = ChessEnv()
			env.update(fen)
		except:
			return abort(400, 'wrong fen format')

		# try to get cache
		with db_lock:
			action = get_cache(app.db_cursor, mode, fen)
		if action is not None:
			return action

		# get pipe_pool
		pipe_pool = None
		with pipe_lock:
			if len(reserved_pipe_pools) > 0:
				pipe_pool = reserved_pipe_pools.pop()
		if pipe_pool is None:
			with model_lock:
				pipe_pool = model.get_pipes(config.play.search_threads)

		# create player
		if mode == 'easy':
			player = GentleChessPlayer(config, pipe_pool)
		else:
			player = ChessPlayer(config, pipe_pool)

		# get action
		manager = Manager()
		ret = manager.dict()
		player_worker = Process(target=get_action, args=(player, env, ret))
		player_worker.start()
		player_worker.join()
		action = ret['action']
		probabilities = ret['probabilities']
		confidence = ret['confidence']

		# move pipe_pool into reserved_pipe_pools
		with pipe_lock:
			reserved_pipe_pools.append(pipe_pool)

		# try to put cache
		with db_lock:
			put_cache(app.db_cursor, mode, fen, probabilities, confidence)

		# return the action
		return {'action': config.labels[action], 'confidence': confidence[action]}

def main(num_thread=None, port=23456):
	if num_thread is not None:
		config.play.search_threads = num_thread

	app.pipe_lock = Lock()
	app.reserved_pipe_pools = []
	app.model_lock = Lock()
	app.model = ChessModel(config)

	db_connection = sqlite3.connect('db.db', isolation_level=None, check_same_thread=False)
	db_connection.row_factory = sqlite3.Row
	app.db_cursor = db_connection.cursor()
	app.db_lock = Lock()

	app.db_cursor.execute('''CREATE TABLE IF NOT EXISTS ActionProbs (
		id INTEGER PRIMARY KEY UNIQUE,
		cacheid INTEGER,
		action INTEGER,
		probability REAL,
		confidence REAL,
		UNIQUE(cacheid, action),
		FOREIGN KEY(cacheid) REFERENCES Cache(id)
	)''')

	app.db_cursor.execute('''CREATE TABLE IF NOT EXISTS Cache (
		id INTEGER PRIMARY KEY UNIQUE,
		mode TEXT,
		fen TEXT,
		UNIQUE(mode, fen)
	)''')

	if not load_best_model_weight(app.model):
		raise RuntimeError('Best model not found!')

	app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
	Fire(main)
