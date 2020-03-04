#!/bin/sh

gunicorn -w 2 -k uvicorn.workers.UvicornWorker starlette_uvicorn_embed:app
