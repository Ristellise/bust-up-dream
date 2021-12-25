import asyncio
import io
import json
import pathlib
import struct
import typing

import PIL.Image
from PIL import Image
from quart import Websocket

from FileAccessor.rackPlaylist import RackReader
from Sources import detect_source
from Sources.AudioSource import AudioSource
from .AudioPlayer import AudioPlayer


class OpusStreamer:

    def __init__(self, broadcast_function, batcheWS=20):
        self.cover = None
        self._prefill = io.BytesIO()
        self.loop: typing.Optional[asyncio.AbstractEventLoop] = None
        self.playlist = RackReader(str(pathlib.Path("Music")))
        self.audioLock = asyncio.Lock()
        self.meta = {}
        self.batchSize = batcheWS
        self.src: typing.Optional[AudioSource] = None
        self.broadcast_func = broadcast_function

    def release_lock(self, err=None):
        if not err:
            self.audioLock.release()
        else:
            print("Locking up due to error. Check.")
            raise err

    async def runner(self, loop):
        print("Starting runner.")
        self.loop = loop
        while True:
            song_fp, cover = self.playlist.get_song(rack_idx=-1)
            self.src = detect_source(song_fp)
            self.meta = dict(self.src.meta.tags)
            await self.audioLock.acquire()
            with Image.open(cover) as im:
                im: PIL.Image.Image = im
                im.thumbnail(size=(512, 512), resample=Image.LANCZOS)
                byteData = io.BytesIO()
                im.save(byteData, format="jpeg", quality=95)
            byteData.seek(0)
            self.cover = byteData.read()
            byteData.close()
            await self.send_meta(i_websocket=None, sync_time=False)
            player = AudioPlayer(self.src, self.binaryCastWS, after=self.release_lock_threadsafe, batch=self.batchSize)
            player.start()
            await self.audioLock.acquire()
            self.audioLock.release()
            self.src.close()

    def binaryCastWS(self, bffer):

        if type(bffer) == list:
            sz = [len(b) for b in bffer]
            pk = [f'H{s}s' for s in sz]
            zp = [v for sub in zip(sz, bffer) for v in sub]
            asyncio.run_coroutine_threadsafe(
                self.broadcast_func(struct.pack(f">{''.join(pk)}", *zp)),
                loop=self.loop)
        else:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_func(bffer),
                loop=self.loop)

    def build_meta(self, sync_time=False):
        meta = self.meta
        meta = {**meta}
        if meta.get('encoder_options'):
            del meta['encoder_options']
        if meta.get('encoder'):
            del meta['encoder']
        if self.src and sync_time:
            meta = {**meta, "time": self.src.seconds}
        meta = {**meta, "event": "meta"}
        return meta

    async def send_meta(self, i_websocket: Websocket = None, sync_time=False):

        meta = self.build_meta(sync_time=sync_time)
        if i_websocket is None:
            self.cast_ws(json.dumps(meta))
        else:
            await i_websocket.send_json(meta)

    def get_loop(self):
        if not self.loop:
            raise Exception
        return self.loop

    def release_lock_threadsafe(self, err=None):
        self.loop.call_soon_threadsafe(self.release_lock, err)

    def cast_ws(self, bffer):
        asyncio.run_coroutine_threadsafe(self.broadcast_func(bffer), loop=self.loop)
