import chess
import random
from fire import Fire
from flask import Flask, request, abort
from flask_restx import Api, Resource
from UCI import ALL_LABELS

MODES = ['easy', 'hard']
MAX_LEVEL = 32

app = Flask(__name__)
api = Api(app)

@api.route('/<string:mode>/<int:level>')
class AI_REST_API(Resource):
	def post(self, mode, level):
		history = request.json

		if not mode in MODES:
			return abort(400, 'wrong mode')

		if not (0 <= level and level < MAX_LEVEL):
			return abort(400, 'wrong level')

		if not isinstance(history, list):
			return abort(400, 'wrong request')

		board = chess.Board()

		for move in history:
			try:
				move = chess.Move.from_uci(move)
			except:
				return abort(400, "wrong history")
			if move in board.legal_moves:
				board.push(move)
			else:
				return abort(400, "wrong history")

		if board.legal_moves:
			return random.choice(list(board.legal_moves)).uci()
		else:
			return abort(400, "no legal move")

if __name__ == "__main__":
	Fire(app.run)
