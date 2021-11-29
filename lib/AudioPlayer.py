import sys
import threading
import time
import traceback
from typing import Optional, Callable, Any

from Sources.AudioSource import AudioSource


class AudioPlayer(threading.Thread):
    BYTE_READ = 20
    DELAY: float = BYTE_READ / 1000.0

    def __init__(self, source: AudioSource, broadcast_func, *, batch=20, after=None):
        threading.Thread.__init__(self)
        self.daemon: bool = True
        self.source: AudioSource = source
        self.after: Optional[Callable[[Optional[Exception]], Any]] = after
        self.broadcast_func = broadcast_func

        self._end: threading.Event = threading.Event()
        self._resumed: threading.Event = threading.Event()
        self._resumed.set()  # we are not paused
        self._current_error: Optional[Exception] = None
        self._lock: threading.Lock = threading.Lock()
        self._batch = batch

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

            ctr = 0
            data = []
            while ctr != self._batch:
                self.loops += 1
                try:
                    data.append(self.source.read())
                    ctr += 20
                except StopIteration:
                    self.stop()
                    break

            play_audio(data)
            next_time = self._start + self.DELAY * self.loops
            # noinspection PyTypeChecker
            delay = max(0, self.DELAY + (next_time - time.perf_counter()) - 0.2) # tiny extra to make playback a bit smoother. hack.
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

    def _set_source(self, source: AudioSource) -> None:
        with self._lock:
            self.source = source
            self.resume()
