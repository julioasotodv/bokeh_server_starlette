import socket


# Not in use. I do not
# use this file in the
#.sh exec:
def on_starting(server):
    socket.SO_REUSEPORT = 15

