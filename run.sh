#!/bin/sh
. .venv/bin/activate
. env.sh
exec gunicorn 'biaoqingbao:create_app()'
