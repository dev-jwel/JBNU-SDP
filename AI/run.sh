PYTHONPATH=src/chess-alpha-zero/src nohup python src/main.py $@ >> log.txt 2>> log.txt &
jobs -p 1
