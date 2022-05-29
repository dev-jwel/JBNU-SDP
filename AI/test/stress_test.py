import json
import grequests
from fire import Fire
import numpy as np
from tqdm import tqdm
from matplotlib import pyplot as plt

fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

def test(url, num_request=10, timeout=60):
	reqs = [
		grequests.post(
			url+'/easy',
			headers={'Content-Type': 'application/json'},
			data=json.dumps({'fen':fen}),
			timeout=timeout
		)
		for _ in range(num_request)
	]

	ret = []

	for resp in grequests.map(reqs):
		if resp is None:
			ret.append(None)
			continue
		ret.append(resp.elapsed.total_seconds())

	return ret

def main(url, max_request=100):
	means = []
	stds = []
	for i in tqdm(range(1, max_request+1)):
		delays = test(url, num_request=i)
		means.append(np.mean(delays))
		stds.append(np.std(delays))

	means = np.array(means)
	stds = np.array(stds)
	lowers = means - stds
	uppers = means + stds

	plt.plot(range(1, max_request+1), means, color='C0')
	plt.fill_between(range(1, max_request+1), lowers, uppers, color='C0', alpha=0.5)
	plt.title('stress test')
	plt.xlabel('num_request')
	plt.ylabel('elapsed time')
	plt.savefig('stress_test.png')

if __name__ == '__main__':
	Fire(main)
