import asyncio
import json
from functools import wraps

import quart
from quart import websocket

from lib import ConfigLoader
from lib.OpusStreamer import OpusStreamer

app = quart.Quart("App")

connected_websockets = set()


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global connected_websockets
        queue = asyncio.Queue()
        connected_websockets.add(queue)
        try:
            return await func(queue, *args, **kwargs)
        finally:
            connected_websockets.remove(queue)

    return wrapper


async def r_broadcast(message):
    for queue in connected_websockets:
        await queue.put(message)


@app.before_first_request
async def opus_streamer():
    config: ConfigLoader.Configurartion = app.config.setdefault('config',
                                                                ConfigLoader.Configurartion('config.ini'))
    print(config.site)
    if app.config.get('streamInstance') is None:
        app.config['streamInstance'] = OpusStreamer(r_broadcast, batcheWS=int(config.site['cachesize']))
    streamInstance = app.config.get('streamInstance')

    lp = asyncio.get_event_loop()
    lp.create_task(streamInstance.runner(lp))


@app.route("/api/cover")
async def collect_cover():
    streamInstance: OpusStreamer = app.config.get('streamInstance')
    if streamInstance.cover is not None:
        return quart.Response(streamInstance.cover, status=200, mimetype="image/jpeg")


@app.route("/api/meta")
async def meta():
    instance = app.config.get('streamInstance')
    if isinstance(instance, OpusStreamer):
        meta = instance.build_meta()
        return quart.jsonify(meta)
    return {}, 404


@app.route("/")
async def index_main():
    config = app.config.get('config')
    return await quart.render_template("index.html", site=config.site, social=config.social)


@app.websocket('/api/stream')
@collect_websocket
async def ws(queue):
    try:
        print("WS Called, sending json text")
        if app.config.get('streamInstance') is None:
            app.config['streamInstance'] = OpusStreamer(r_broadcast)
        await app.config['streamInstance'].send_meta(websocket, sync_time=True)
        print("WS Accepted")
        while True:
            data = await queue.get()
            if isinstance(data, dict) or isinstance(data, str):
                if isinstance(data, str):
                    data = json.loads(data)
                await websocket.send_json(data)
            else:
                await websocket.send(data)
    except asyncio.CancelledError:
        print("WS Closed")


if __name__ == '__main__':
    app.run()
