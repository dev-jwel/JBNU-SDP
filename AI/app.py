import chess
import random
from fire import Fire
from flask import Flask, request, abort, current_app
from flask_restx import Api, Resource

from threading import Lock
from chess_zero.agent.player_chess import ChessPlayer
from chess_zero.agent.player_chess import GentleChessPlayer
from chess_zero.config import Config, PlayWithHumanConfig
from chess_zero.env.chess_env import ChessEnv
from chess_zero.agent.model_chess import ChessModel
from chess_zero.lib.model_helper import load_best_model_weight
from chess_zero.lib.logger import setup_logger

MODES = ['easy', 'hard']

config = Config(config_type='normal')
config.resource.create_directories()
setup_logger(config.resource.main_log_path)
PlayWithHumanConfig().update_play_config(config.play)

app = Flask(__name__)
api = Api(app)

@api.route('/<string:mode>')
class AI_REST_API(Resource):
	def post(self, mode):
		# get request
		req = request.json

		pipe_lock = current_app.pipe_lock
		reserved_pipe_pools = current_app.reserved_pipe_pools
		model_lock = current_app.model_lock
		model = current_app.model

		if not mode in MODES:
			return abort(400, 'wrong mode')
		if 'fen' not in req:
			return abort(400, 'there is no fen in the request')

		# create env
		try:
			env = ChessEnv()
			env.update(req['fen'])
		except:
			return abort(400, 'wrong fen format')

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
		action = player.action(env)

		# move pipe_pool into reserved_pipe_pools
		with pipe_lock:
			reserved_pipe_pools.append(pipe_pool)

		# return the action
		return action

def main(num_thread=None, port=23456):
	if num_thread is not None:
		config.play.search_threads = num_thread

	app.pipe_lock = Lock()
	app.reserved_pipe_pools = []
	app.model_lock = Lock()
	app.model = ChessModel(config)

	if not load_best_model_weight(app.model):
		raise RuntimeError('Best model not found!')

	app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
	Fire(main)
