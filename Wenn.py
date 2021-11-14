import asyncio
import base64
import json
import pathlib
import random
import sys
import threading
import time
import traceback
import typing
import zlib
from functools import wraps
from typing import Optional, Callable, Any

import io

import quart
from quart import websocket
from . import oggparse

app = quart.Blueprint("Wenn", "wenn", )


class OpusAudioSource:

    def __init__(self, fp):
        self.fp = fp
        self.fp_a = open(self.fp, "rb")
        self.stream = oggparse.OggStream(self.fp_a)
        self.packet_iter = self.stream.iter_packets()

    def read(self):
        return next(self.packet_iter)

    def __del__(self):
        self.fp_a.close()


class AudioPlayer(threading.Thread):
    BYTE_READ = 20
    DELAY: float = BYTE_READ / 1000.0

    def __init__(self, source: OpusAudioSource, broadcast_func, *, after=None):
        threading.Thread.__init__(self)
        self.daemon: bool = True
        self.source: OpusAudioSource = source
        self.after: Optional[Callable[[Optional[Exception]], Any]] = after
        self.broadcast_func = broadcast_func

        self._end: threading.Event = threading.Event()
        self._resumed: threading.Event = threading.Event()
        self._resumed.set()  # we are not paused
        self._current_error: Optional[Exception] = None
        self._lock: threading.Lock = threading.Lock()

        if after is not None and not callable(after):
            raise TypeError('Expected a callable for the "after" parameter.')

    def _do_run(self) -> None:
        self.loops = 0
        self._start = time.perf_counter()

        # getattr lookup speed ups
        play_audio = self.broadcast_func
        while not self._end.is_set():
            # are we paused?
            if not self._resumed.is_set():
                # wait until we aren't
                self._resumed.wait()
                continue

            self.loops += 1
            data = b''
            try:
                data = self.source.read()
            except StopIteration:
                self.stop()
                break

            if not data:
                self.stop()
                break
            play_audio(data)
            next_time = self._start + self.DELAY * self.loops
            # noinspection PyTypeChecker
            delay = max(0, self.DELAY + (next_time - time.perf_counter()))
            time.sleep(delay)

    def run(self) -> None:
        try:
            self._do_run()
        except Exception as exc:
            self._current_error = exc
        finally:
            self._call_after()

    def _call_after(self) -> None:
        error = self._current_error

        if self.after is not None:
            try:
                self.after(error)
            except Exception as exc:

                exc.__context__ = error
                traceback.print_exception(type(exc), exc, exc.__traceback__)
        elif error:
            msg = f'Exception in audio thread {self.name}'
            print(msg, file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__)

    def stop(self) -> None:
        self._end.set()
        self._resumed.set()

    def resume(self) -> None:
        self.loops = 0
        self._start = time.perf_counter()
        self._resumed.set()

    def is_playing(self) -> bool:
        return self._resumed.is_set() and not self._end.is_set()

    def is_paused(self) -> bool:
        return not self._end.is_set() and not self._resumed.is_set()

    def _set_source(self, source: OpusAudioSource) -> None:
        with self._lock:
            self.source = source
            self.resume()


class PlaylistReader:

    def __init__(self, m3u8_root, filename_glob):
        self.queued = []
        self.m3u8 = None
        self.fs = None
        self.check = None
        self.songs = []
        self.path = (m3u8_root, filename_glob)

    def read_pl(self):
        m3u8_n = list(pathlib.Path(self.path[0]).glob(self.path[1]))[-1]
        fs_n = m3u8_n.read_text(encoding="utf-8 sig").strip()
        n_chk = (zlib.crc32(fs_n.encode()) & 0xffffffff)
        if self.check != n_chk:
            self.m3u8 = m3u8_n
            self.fs = fs_n
            self.check = n_chk
            self.songs = fs_n.split("\n")
            t_songs = []
            for i in self.songs:
                if i.startswith('#'):
                    pass
                else:
                    t_songs.append(i)
            self.songs = t_songs


    def get_song(self):
        self.read_pl()
        if len(self.queued) <= 0:
            self.queued = self.songs.copy()
            random.shuffle(self.queued)
            self.queued = self.queued[:10]
        return str(pathlib.Path(self.path[0]).joinpath(self.queued.pop(0)))


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


class OpusStreamer:

    def __init__(self):
        self.cover = {"cover": ""}
        self._prefill = io.BytesIO()
        self.loop: typing.Optional[asyncio.AbstractEventLoop] = None
        self.playlist = PlaylistReader(str(pathlib.Path("Music")), "Wenn_*.m3u8")
        self.audioLock = asyncio.Lock()
        self.meta = {}

    def release_lock(self, err=None):
        if not err:
            self.audioLock.release()
        else:
            print("Locking up due to error. Check.")
            raise err

    async def runner(self, loop):
        print("Starting runner")
        self.loop = loop
        while True:
            song_fp = None
            if song_fp is None:
                song_fp = self.playlist.get_song()
            src = OpusAudioSource(song_fp)
            self.meta = dict(src.stream.meta.tags)
            await self.audioLock.acquire()
            self.cast_ws(json.dumps(self.meta))
            cover = list(pathlib.Path(song_fp).resolve().parent.glob("cover.*"))
            if len(cover) == 0:
                cover = list(pathlib.Path(song_fp).resolve().parent.glob("Cover.*"))
                if len(cover) == 0:
                    cover = [pathlib.Path(self.playlist.path[0]).joinpath("Cover.jpg")]
            self.cover = {"cover": base64.b64encode(cover[0].read_bytes()).decode()}
            self.cast_ws(json.dumps(self.cover))
            player = AudioPlayer(src, self.cast_ws, after=self.release_lock_threadsafe)
            player.start()
            await self.audioLock.acquire()
            self.audioLock.release()

    def get_loop(self):
        if not self.loop:
            raise Exception
        return self.loop

    def release_lock_threadsafe(self, err=None):
        self.loop.call_soon_threadsafe(self.release_lock, err)

    def cast_ws(self, bffer):
        asyncio.run_coroutine_threadsafe(r_broadcast(bffer), loop=self.loop)


streamInstance: typing.Optional[OpusStreamer] = None


@app.before_app_first_request
async def opus_streamer():
    global streamInstance  # Cursed.
    if streamInstance is None:
        streamInstance = OpusStreamer()

    lp = asyncio.get_event_loop()
    lp.create_task(streamInstance.runner(lp))


@app.route("/")
async def index_main():
    return await quart.render_template("index.html")


@app.websocket('//stream')
@app.websocket('/stream')
@collect_websocket
async def ws(queue):
    try:
        print("WS Called, sending json text")
        await websocket.send_json(streamInstance.meta)
        await websocket.send_json(streamInstance.cover)
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

app.run()