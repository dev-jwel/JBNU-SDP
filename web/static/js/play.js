import { Chess } from './chess.js'

let game = new Chess()
let selected_square_button = null

let color_black = "#eeeed2"
let color_white = "#769656"
let color_select = "#FFFF00"

window.square_click_callback = function(square) {
	let square_button = document.getElementById(square).children[0]
	if (square_button === null) {
		return
	}

	if (selected_square_button === null) {
		selected_square_button = square_button
		change_color(square_button, color_select)
	} else {
		if (selected_square_button === square_button) {
			selected_square_button = null
			change_color(square_button, null)
		} else {
			change_color(selected_square_button, null)
			selected_square_button = square_button
			change_color(square_button, color_select)
		}
	}

}

function change_color(square_button, color) {
	if (square_button === null) {
		return
	}

	if (color === null) {
		if (square_button.classList.contains("black-button")) {
			color = color_black
		} else if (square_button.classList.contains("white-button")) {
			color = color_white
		} else {
			return
		}
	}
	square_button.style.backgroundColor = color
}

window.predict = function(mode, fen=game.fen(), on_success, on_error) {
	$.ajax({
		url: "/predict",
		type: "POST",
		datatype: "json",
		data: {
			"mode": mode,
			"fen": fen
		},
		success: function(res) {
			console.log('res')
			console.log(res)
			on_success(res)
		},
		error: function(error) {
			console.log('error')
			console.log(error)
			on_error()
		},
		timeout: 60000
	})
}

window.debug = function() {
	console.log(game.board())
}

for (let row of game.board()) {
	for (let square of row) {
		if (square === null) continue

		let color = null
		let piece = null

		if (square.color === "b") {
			color = "Black"
		} else if (square.color === "w") {
			color = "White"
		}

		if (square.type === "k") {
			piece = "King"
		} else if (square.type === "q") {
			piece = "Queen"
		} else if (square.type === "r") {
			piece = "Rook"
		} else if (square.type === "b") {
			piece = "Bishop"
		} else if (square.type === "n") {
			piece = "Knight"
		} else if (square.type === "p") {
			piece = "Pawn"
		}

		let square_image = document.getElementById(square.square).children[0].children[0]
		square_image.src = "/static/img/" + color + piece + ".png"
	}
}

/*
class WebServerWraper {
	constructor(host, port) {
		this.url = "http://" + host + ":" + port
	}

	add_history(mode, user_color, history) {
		ret = null
		$.ajax({
			url: this.url + "/add_history",
			type: "POST",
			datatype: "json",
			data: {
				"mode": mode,
				"user_color": user_color,
				history: history
			},
			success: function(res) {
				ret = JSON.parse(res)
			},
			error: function(error) {}
		})
		return ret
	}
}

class Game {
	constructor(mode, user_color) {
		this.mode = mode
		this.user_color = user_color
		this.board = new Chess()
		this.web_server = WebServerWraper(HOST, PORT)

		if(user_color == "black") {
			move = this.web_server.predict(this.mode, this.board.fen())
			this.board.make_move(move)
		}
	}

	has_piece(square) {
		return this.board.get(square) !== null
	}

	make_move(move) {
		this.board.make_move(move)
		move = this.web_server.predict(this.mode, this.board.fen())
		this.board.make_move(move)
	}

	get_legal_moves(square) {
		return this.board.moves({square: square})
	}

	undo() {
		this.board.undo()
		this.board.undo()
	}

	get_hint() {
		return this.web_server.predict(this.mode, this.board.fen())
	}
}

class GameClickHandler {
	constructor(mode, user_color) {
		this.game = Game(mode, user_color)
		this.selected_square = null
	}

	clear_color() {
		for(var rank of [1,2,3,4,5,6,7,8]) {
			for(var file in 'abcdefgh') {
				SquareRenderer.change_color(SquareRenderer.DEFAULT, file+rank)
			}
		}
	}

	board_click_callback(square) {
		if(!this.game.has_piece(square)) {
			return
		}

		this.clear_color()

		if(this.selected_square !== square) {
			for(var legal_square of this.game.get_legal_moves(square)) {
				SquareRenderer.change_color(SquareRenderer.LEGAL_MOVE, legal_square)
			}

			SquareRenderer.change_color(SquareRenderer.SELECTED, legal_square)
			this.selected_square = square
		} else {
			this.selected_square = null
		}
	}

	hint_click_callback() {
		this.selected_square = null
		this.clear_color()
		hint = this.game.get_hint()
		move = chess.move(hint)
		SquareRenderer.change_color(SquareRenderer.SUGGESTION, move.from)
		SquareRenderer.change_color(SquareRenderer.SUGGESTION, move.to)
	}

	undo_click_callback() {
		this.selected_square = null
		this.clear_color()
		this.game.undo()
	}
}

class SquareRenderer {
	static DEFAULT = "#??????"
	static SELECTED = "#??????"
	static LEGAL_MOVE = "#??????"
	static SUGGESTION = "#??????"

	static change_color(color, square) {
		// TODO
		// select dom object using square
		// set object's color
	}
}

class OptionSelector {
	static select_option(title, options, callbacks) {
		// TODO
		// create new div object
		// add title into object
		// add options with click callback
		// add popup close callback
		// append object into document
	}
}
*/
