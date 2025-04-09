#!/bin/bash
gunicorn main:app --bind 0.0.0.0:$PORT
chmod +x start.sh