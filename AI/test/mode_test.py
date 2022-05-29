import json
import chess
import requests
from fire import Fire
from matplotlib import pyplot as plt
from multiprocessing import Process, Manager

def easy_vs_hard(url, easy_color, ret):
	color = 'white'
	board = chess.Board()

	if easy_color == 'white':
		color_to_mode = {'black': 'hard', 'white': 'easy'}
	else:
		color_to_mode = {'black': 'easy', 'white': 'hard'}

	while board.outcome() == None:
		mode = color_to_mode[color]
		fen = board.fen()

		resp = requests.post(
			url + '/' + mode,
			headers={'Content-Type': 'application/json'},
			data=json.dumps({'fen':fen})
		)

		result = json.loads(resp.text)
		action = result['action']
		confidence = result['confidence']
		if mode == 'hard':
			confidence *= -1

		board.push_uci(action)
		ret.append({'action': action, 'confidence': confidence})

		if color == 'black':
			color = 'white'
		else:
			color = 'black'

def save_result(history, prefix):
	plt.plot(range(len(history)), history)
	plt.savefig(prefix + 'easy_vs_hard.png')
	plt.clf()

def main(url):
	easy_black_results = []
	easy_white_results = []
	processes = []

	for i in range(5):
		l = Manager().list()
		easy_black_results.append(l)
		p = Process(target=easy_vs_hard, args=(url, 'black', l))
		p.start()
		processes.append(p)

		l = Manager().list()
		easy_white_results.append(l)
		p = Process(target=easy_vs_hard, args=(url, 'white', l))
		p.start()
		processes.append(p)

	for p in processes:
		p.join()

	easy_black_results = [list(r) for r in easy_black_results]
	easy_white_results = [list(r) for r in easy_white_results]

	with open('mode_test.json', 'w') as f:
		json.dump({
			'black': easy_black_results,
			'white': easy_white_results
		}, f)

if __name__ == '__main__':
	Fire(main)
