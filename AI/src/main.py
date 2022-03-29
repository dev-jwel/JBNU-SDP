import random
from fire import Fire
from flask import Flask, request, abort
from flask_restx import Api, Resource

game_names = ['gomoku', 'chess', 'othello']
modes = ['easy', 'hard']
colors = ['black', 'white']
max_level = 32

map_size_for_game = {
	'gomoku' : 15,
	'chess' : 8,
	'othello' : 8
}

chess_pieces = [
	'king',
	'queen',
	'rook',
	'bishop',
	'knight',
	'pawn'
]

def is_valid_request(game_name, request):

	if not request.get('color', None) in colors:
		return False

	turn = request.get('turn', None)
	if turn == None or turn > 1:
		return False

	map = request.get('map', None)
	if map == None:
		return False

	return is_valid_map(game_name, map)

def is_valid_map(game_name, map):
	if not is_valid_map_size(game_name, map):
		return False

	for line in map:
		for element in line:
			if not is_valid_element(game_name, element):
				return False

	return True

def is_valid_map_size(game_name, map):
	if len(map) != map_size_for_game[game_name]:
		return False

	for line in map:
		if len(line) != map_size_for_game[game_name]:
			return False

	return True

def is_valid_element(game_name, element):
	if game_name == 'gomoku':
		return element in [0,1,2]
	elif game_name == 'othello':
		return element in [0,1,2]

	elif game_name == 'chess':
		if element == None:
			return True
		if not isinstance(element, dict):
			return False
		if not element.get('color', None) in colors:
			return False
		if not element.get('piece', None) in chess_pieces:
			return False
		return True

app = Flask(__name__)
api = Api(app)

@api.route('/<string:game_name>/<string:mode>/<int:level>')
class AI_REST_API(Resource):
	def post(self, game_name, mode, level):
		req = request.json

		if not is_valid_request(game_name, req):
			abort(400)

		if game_name == 'chess':
			return {'error' : 'not implemented yet'}

		map_size = map_size_for_game[game_name]

		trial = 1
		row, col = random.randint(0, map_size-1), random.randint(0, map_size-1)
		while trial < 100 and req['map'][row][col] != 2:
			trial += 1
			row, col = random.randint(0, map_size-1), random.randint(0, map_size-1)

		if req['map'][row][col] == 2:
			return [row, col]
		else:
			return {'error' : 'failed to find empty space'}

if __name__ == "__main__":
	Fire(app.run)
