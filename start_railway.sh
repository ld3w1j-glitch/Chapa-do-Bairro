#!/bin/sh
python scripts/railway_init_db.py
gunicorn run:app --bind 0.0.0.0:$PORT
