def create_uci_labels():
	labels_array = []
	letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
	numbers = ['1', '2', '3', '4', '5', '6', '7', '8']
	promoted_to = ['q', 'r', 'b', 'n']

	# common moves
	for l1 in range(8):
		for n1 in range(8):
			night_moves = [(-2, -1), (-1, -2), (-2, 1), (1, -2), (2, -1), (-1, 2), (2, 1), (1, 2)]
			destinations = []
			destinations += [(t, n1) for t in range(8)] # horizontal
			destinations += [(l1, t) for t in range(8)] # vertical
			destinations += [(l1 + t, n1 + t) for t in range(-7, 8)] # diagonal
			destinations += [(l1 + t, n1 - t) for t in range(-7, 8)] # diagonal
			destinations += [(l1 + a, n1 + b) for (a, b) in night_moves] # night moves

			for (l2, n2) in destinations:
				if (l1, n1) != (l2, n2) and l2 in range(8) and n2 in range(8):
					move = letters[l1] + numbers[n1] + letters[l2] + numbers[n2]
					labels_array.append(move)

	# promotions
	for l1 in range(8):
		l = letters[l1]
		for p in promoted_to:
			labels_array.append(l + '2' + l + '1' + p)
			labels_array.append(l + '7' + l + '8' + p)
			if l1 > 0:
				l_l = letters[l1 - 1]
				labels_array.append(l + '2' + l_l + '1' + p)
				labels_array.append(l + '7' + l_l + '8' + p)
			if l1 < 7:
				l_r = letters[l1 + 1]
				labels_array.append(l + '2' + l_r + '1' + p)
				labels_array.append(l + '7' + l_r + '8' + p)
	return labels_array

ALL_LABELS = create_uci_labels()
