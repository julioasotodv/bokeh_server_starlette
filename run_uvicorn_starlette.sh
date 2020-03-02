#!/bin/sh

uvicorn --loop=uvloop starlette_server:app
