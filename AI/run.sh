PYTHONPATH=chess-alpha-zero/src nohup python app.py $@ >> log.txt 2>> log.txt &
jobs -p 1
