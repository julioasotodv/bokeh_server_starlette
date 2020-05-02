# Stdlib imports
try:
    import asyncio
except ImportError:
    raise RuntimeError("This example requries Python3 / asyncio")

import socket

# Bokeh plotting imports
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider, Paragraph
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.themes import Theme

# Bokeh Server-y imports
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import server_document
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
#from bokeh.server.util import bind_sockets

# Panel imports
import param
import panel as pn

# Starlette imports
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

# Tornado imports
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.netutil import bind_sockets
from tornado.web import StaticFileHandler

# Jinja imports
from jinja2 import Environment, FileSystemLoader


if __name__ == '__main__':
    print('This script is intended to be run with gunicorn/uvicorn. e.g.')
    print()
    print('    uvicorn --workers=4 starlette_uvicorn_embed:app')
    print()
    print('or')
    print()
    print('    gunicorn -w 4 -k uvicorn.workers.UvicornWorker starlette_uvicorn_embed:app')
    print()
    print('will start the app on four processes')
    import sys
    sys.exit()

# Get ip in network:
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("192.168.1.1", 80))
ip = s.getsockname()[0]
s.close()

# Monkey patch for Anaconda, since
# it is unaware whether the Linux
# kernel has got SO_REUSEPORT or not...
#socket.SO_REUSEPORT = 15

# Startup options for Bokeh Server:
socket = bind_sockets(8001, 
                      address="",
                      #reuse_port=True # Unavailable in some platforms, dependes on SO_REUSEPORT being 15
                     )[0]
port = socket.getsockname()[1]

# Startup options for Starlette:
templates = Jinja2Templates(directory='templates')


# Bokeh Applications:
def bkapp(curdoc):
    import time
    time.sleep(5)

    df = sea_surface_temperature.copy()
    source = ColumnDataSource(data=df)

    plot = figure(x_axis_type='datetime', y_range=(0, 25), y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line('time', 'temperature', source=source)

    def callback(attr, old, new):
        if new == 0:
            data = df
        else:
            data = df.rolling('{0}D'.format(new)).mean()
        source.data = data
    plot.sizing_mode = "stretch_both"

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change('value', callback)

    paragraph = Paragraph(text="IOloop's id: %s" % str(id(bokeh_server.io_loop.asyncio_loop)))

    row = pn.Row(slider, plot, name="chart_1")
    row.sizing_mode = "stretch_both"
    row.server_doc(curdoc)

    other_figure = figure(title="Jajaja")
    other_figure.scatter(x=[1,2,3], y=[4,5,6])
    other_figure.sizing_mode = "stretch_both"
    pn.Pane(other_figure, name="chart_2").server_doc(curdoc)

    curdoc.theme = Theme(filename="theme.yaml")

    # Options for Jinja template rendered by the Bokeh Server
    # (as opposed of by Starlette):
    curdoc.template = (Environment(loader=FileSystemLoader(searchpath="templates"))
                       .get_template("index.html")
                       )
    curdoc.template_variables["rendered_by_bokeh_server"] = True


# Starlette endpoints (similar to
# Flask's @app.route):
async def homepage(request):
    bokeh_page_url = request.url_for('bokeh_page_url')
    return templates.TemplateResponse("start.html", 
                                     {"request": request}
                                     )

async def redirect_bokeh(request):
    return templates.TemplateResponse("redirect_to_bokeh_server.html",
                                      {"request": request,
                                      "bokeh_page_url": "http://%s:%s" % (request.url.hostname, 8001),
                                      "rendered_by_bokeh_server": False}
                                      )


# Bokeh Server configuration and startup:
#
# To get Gunicorn/Uvicorn's multi-worker
# working, we need to create the Bokeh Server
# using the low level APIs. Inspired by
# https://github.com/bokeh/bokeh/blob/master/examples/howto/server_embed/flask_gunicorn_embed.py

bokeh_app = Application(FunctionHandler(bkapp))

bokeh_tornado = BokehTornado({'/bkapp': bokeh_app},
                              extra_patterns=[(r'/static_assets/(.*)', StaticFileHandler, {'path': "static"})],
                              extra_websocket_origins=["localhost:8000", "localhost:8001", '%s:8001' % (ip)],
                              )

bokeh_http = HTTPServer(bokeh_tornado)
bokeh_http.add_socket(socket)

bokeh_server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
bokeh_server.start()

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware


# Starlette App creation
app = Starlette(debug=True, routes=[
    Route('/', endpoint=homepage, name='homepage_url'),
    Mount('/static', StaticFiles(directory='static'), name='static'),
    Route('/bokeh', endpoint=redirect_bokeh, name='bokeh_page_url')
    ]
)
