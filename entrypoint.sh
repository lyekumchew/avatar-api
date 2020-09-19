#!/bin/sh

python3 manage.py makemigrations avatar_core
python3 manage.py makemigrations avatar_user
python3 manage.py makemigrations avatar_map_matching
python3 manage.py makemigrations avatar_simulator
python3 manage.py migrate

exec "$@"