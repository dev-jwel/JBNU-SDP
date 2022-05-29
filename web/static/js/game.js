import { Chess } from './chess.js'

let game = new Chess()
let selected_square = null
let selected_square_button = null
let is_predict_requested = false

let user_color = null
let ai_color = null
let mode = "easy"

let color_black = "#EEEED2"
let color_white = "#769656"
let color_select = "#FFFF00"
let color_legal = "#FF0000"
let color_ai = "#0000FF"

function initialze_game() {
	if (Math.random() < 0.5) {
		user_color = "black"
		ai_color = "white"
	} else {
		user_color = "white"
		ai_color = "black"
	}

	let css = user_color + "-user.css"
	let head = document.getElementsByTagName("head")[0]
	let link = document.createElement("link")
	link.rel = "stylesheet"
	link.href = "static/css/" + css
	head.appendChild(link)

	render_board()

	if (ai_color == "white") {
		ai_move(mode, true)
	}
}

function render_board() {
	for(const rank of ["1","2","3","4","5","6","7","8"]) {
		for(const file of ["a", "b", "c", "d", "e", "f", "g", "h"]) {
			let square = file + rank
			let square_image = document.getElementById(square).children[0].children[0]
			square_image.removeAttribute("src")
			square_image.src = "/static/img/Empty.png"
		}
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
}

function square_click_callback(square) {
	let square_button = document.getElementById(square).children[0]
	if (square_button === null) {
		return
	}

	if (is_predict_requested) {
		return
	}

	// first select
	if (selected_square === null) {
		if (game.get(square) !== null) {
			let legal_moves = game.moves({square: square, verbose: true})
			if (legal_moves.length > 0) {
				clear_color()
				selected_square = square
				selected_square_button = square_button
				change_color(square_button, color_select)
				for (const legal_move of legal_moves) {
					let legal_square = legal_move.to
					let legal_square_button = document.getElementById(legal_square).children[0]
					change_color(legal_square_button, color_legal)
				}
			}
		}
	}

	// deselect
	else if (square_button === selected_square_button) {
		selected_square = null
		selected_square_button = null
		clear_color()
	}

	// move
	else {
		let legal_squares = []
		for (let legal_move of game.moves({square: selected_square, verbose: true})) {
			legal_squares.push(legal_move.to)
		}

		if (legal_squares.includes(square)) {
			// TODO: add promotion
			game.move({from: selected_square, to: square}, {sloppy: true})
			if (game.game_over()) {
				finish_game()
				return
			}

			selected_square = null
			selected_square_button = null
			clear_color()
			render_board()

			ai_move(mode, true)
			if (game.game_over()) {
				finish_game()
				return
			}

			render_board()
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

function clear_color() {
	for(const rank of ["1","2","3","4","5","6","7","8"]) {
		for(const file of ["a", "b", "c", "d", "e", "f", "g", "h"]) {
			let square = file + rank
			let button = document.getElementById(square).children[0]
			change_color(button, null)
		}
	}
}

function predict(mode, fen, on_success, on_error, on_complete) {
	$.ajax({
		url: "/predict",
		type: "POST",
		datatype: "json",
		data: {
			"mode": mode,
			"fen": fen
		},
		success: on_success,
		error: on_error,
		complete: on_complete,
		timeout: 60000
	})
}

function ai_move(mode, apply_move) {
	if (is_predict_requested) {
		return
	}

	document.getElementById("status").innerHTML = "requesting..."
	is_predict_requested = true

	predict (
		mode,
		game.fen(),
		function (res) {
			console.log(res)
			let move = game.move(res["action"], {sloppy: true})
			if (!apply_move) {
				game.undo()
			}

			console.log(move)

			render_board()
			let from_square_button = document.getElementById(move.from).children[0]
			let to_square_button = document.getElementById(move.to).children[0]
			change_color(from_square_button, color_ai)
			change_color(to_square_button, color_ai)
		},
		function (error) {
			alert('failed to request')
		},
		function () {
			document.getElementById("status").innerHTML = "your turn"
			is_predict_requested = false
		}
	)
}

function finish_game() {
	let history = []
	for (let move of game.history({verbose: true})) {
		history.push(move.from + move.to)
	}

	if (!anonymous) {
		$.ajax({
			url: "/add-history",
			type: "POST",
			datatype: "json",
			data: {
				"mode": mode,
				"player-color": user_color,
				"history": history.join(',')
			},
			error: function (error) {
				console.log(error)
			}
		})
	}

	alert("game over!")

	if (!anonymous) {
		location.href = "/history-page"
	} else {
		location.href = "/"
	}
}

function change_mode() {
	if (mode === "easy") {
		mode = "hard"
	} else {
		mode = "easy"
	}

	document.getElementById("mode").innerHTML = mode
}

function hint() {
	if (is_predict_requested) {
		return
	}
	selected_square = null
	selected_square_button = null
	clear_color()
	ai_move("hard", false)
}

function undo() {
	if (is_predict_requested) {
		return
	}
	if (game.history().length >= 2) {
		game.undo()
		game.undo()
		render_board()
		clear_color()
	}
}

// debug only
function auto_single(is_my_turn) {
	if (game.game_over()) {
		finish_game()
		return
	}

	let m = mode
	if (!is_my_turn) {
		m = "hard"
	}

	predict (
		m,
		game.fen(),
		function (res) {
			console.log(res)
			let move = game.move(res["action"], {sloppy: true})
			console.log(move)

			render_board()
			clear_color()
			let from_square_button = document.getElementById(move.from).children[0]
			let to_square_button = document.getElementById(move.to).children[0]
			change_color(from_square_button, color_ai)
			change_color(to_square_button, color_ai)

			auto_single(!is_my_turn)
		},
		function (error) {
			alert('failed to request')
		},
		function () {
		}
	)
}
function auto() {
	if (!is_predict_requested) {
		document.getElementById("status").innerHTML = "AUTO"
		is_predict_requested = true
		auto_single(true)
	}
}

window.game = game
window.initialze_game = initialze_game
window.square_click_callback = square_click_callback
window.change_mode = change_mode
window.render_board = render_board
window.hint = hint
window.undo = undo
