try:
    import asyncio
except ImportError:
    raise RuntimeError("This example requries Python3 / asyncio")

# Bokeh plotting imports
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.themes import Theme

# Bokeh Server-y imports
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import server_document
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets

# Starlette imports
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates

# Tornado imports
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


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

# Startup ptions for Bokeh Server:
socket, port = bind_sockets("localhost", 0)

# Startup options for Starlette:
templates = Jinja2Templates(directory='templates')


# Bokeh Applications:
def bkapp(doc):
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
        source.data = ColumnDataSource(data=data).data

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change('value', callback)

    doc.add_root(column(slider, plot))

    doc.theme = Theme(filename="theme.yaml")

# Starlette endpoints (similar to
# Flask's @app.route):
async def homepage(request):
    bokeh_page_url = request.url_for('bokeh_page_url')
    return HTMLResponse('<html><body><h1>Hello!</h1><p>Click <a href="%s">here</a> to go to a Bokeh chart</p></body></html>' % bokeh_page_url)

async def serve_bokeh_plot(request):
    script = server_document('http://localhost:%d/bkapp' % port)
    return templates.TemplateResponse('embed.html', {'request': request,
                                                     'script': script, 
                                                     'framework':('Starlette running on port %d ' % port) +
                                                                 ('with event loop %s' % str(bokeh_server.io_loop.asyncio_loop))
                                                    }
                                    )

# Bokeh Server configuration and startup:
#
# To get Gunicorn/Uvicorn's multi-worker
# working, we need to create the Bokeh Server
# using the low level APIs. Inspired by
# https://github.com/bokeh/bokeh/blob/master/examples/howto/server_embed/flask_gunicorn_embed.py
bokeh_app = Application(FunctionHandler(bkapp))

bokeh_tornado = BokehTornado({'/bkapp': bokeh_app}, extra_websocket_origins=['localhost:8000'])
bokeh_http = HTTPServer(bokeh_tornado)
bokeh_http.add_sockets(socket)

bokeh_server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
bokeh_server.start()

# Starlette App creation
app = Starlette(debug=False, routes=[
    Route('/', endpoint=homepage, name='homepage_url'),
    Route('/bokeh', endpoint=serve_bokeh_plot, name='bokeh_page_url')
])
