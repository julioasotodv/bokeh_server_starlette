from bokeh.embed import server_document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates


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


templates = Jinja2Templates(directory='templates')

async def homepage(request):
    script = server_document('http://localhost:6969/bkapp')
    return templates.TemplateResponse("embed.html", {"request": request,
                                                     "script":script, 
                                                     "framework":"Starlette"})

#uvloop.install()

bokeh_server = Server({'/bkapp': bkapp}, port=6969, allow_websocket_origin=["localhost:8000"])
bokeh_server.start()
print(bokeh_server.io_loop.asyncio_loop)

app = Starlette(debug=True, routes=[
    Route('/', homepage),
])

