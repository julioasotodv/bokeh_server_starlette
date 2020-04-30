#!/bin/sh

gunicorn -b 0.0.0.0:8000 -w 1 -k uvicorn.workers.UvicornWorker --log-level debug starlette_uvicorn_embed:app
