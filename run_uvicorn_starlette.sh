#!/bin/sh

gunicorn -w 2 -k uvicorn.workers.UvicornWorker --log-level debug starlette_uvicorn_embed:app
