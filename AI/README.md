# AI server

Install dependencies in `AI/requirements.txt` and `AI/src/chess-alpha-zero/requirements.txt`.

Run this prototype by typing `./run.sh`.

You can use another port by using argument `--port YOUR-PORT` while default is `23456`.

This script prints pid so you can kill this.

Note: you may face `Too many open files` error. Type `ulimit -Sn unlimited` to avoid this.
