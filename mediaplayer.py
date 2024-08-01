import threading
import time
import keyboard
import pygetwindow
import vlc
from states import States


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


def vlc_foreground_window():
    window_title = str(pygetwindow.getActiveWindowTitle())
    return window_title.startswith("VLC ")


class MediaPlayer:
    def __init__(self, movietron):
        self._movietron = movietron
        self._instance = vlc.Instance()
        self._player = self._instance.media_player_new()
        self._media_path = None
        self._quit_event = None
        self.running_time = 0

    def start(self, movie_path, running_time=0, duration_ms=0):
        self._media_path = movie_path
        self.set_media(movie_path)
        self.play(running_time, duration_ms)

    def set_media(self, movie_path):
        media = self._instance.media_new(movie_path)
        self._player.set_media(media)

    def play(self, running_time, duration):
        self._quit_event = threading.Event()
        self._player.play()
        self._player.audio_set_volume(100)
        self.set_position(running_time, duration)

        self._change_state()

    @threaded
    def _change_state(self):
        time_to_skip_s = 10
        while not self._quit_event.is_set():
            def handle_timeout():
                pass

            timer = threading.Timer(3, handle_timeout)
            timer.start()

            if self._is_ended():
                self._end()

            duration = self._duration() / 1000
            running_time = self._running_time() / 1000
            volume = self._player.audio_get_volume()
            vol_in_dec = 5

            if vlc_foreground_window():
                key = keyboard.read_key()
                if key == 'space':
                    self._pause()
                if key == 'esc':
                    self._quit()
                if key == 'left':
                    self._player.set_position((running_time - time_to_skip_s) / duration)
                if key == 'right':
                    self._player.set_position((running_time + time_to_skip_s) / duration)
                if key == 'up':
                    self._player.audio_set_volume(volume + vol_in_dec)
                if key == 'down':
                    self._player.audio_set_volume(volume - vol_in_dec)

            timer.cancel()
            time.sleep(0.30)

    def set_position(self, running_time, duration):
        if running_time and running_time > 0:
            running_time_s = running_time / 1000
            duration_s = duration / 1000
            skip_to_s = running_time_s / duration_s
            self._player.set_position(skip_to_s)
    def _pause(self):
        if vlc_foreground_window():
            if self._is_playing():
                self._player.set_pause(1)
            else:
                self._player.play()

    def _quit(self):
        if vlc_foreground_window():
            running_time = 0
            if self._running_time() < self._duration():
                running_time = self._running_time()
            self._movietron.end_movie(self._media_path, running_time)
            self._player.stop()
            self._quit_event.set()

    def _end(self):
        self._movietron.end_movie(self._media_path)
        self._player.stop()
        self._quit_event.set()

    def _is_paused(self):
        return self._state() == States.PAUSED.value

    def _is_playing(self):
        return self._state() == States.PLAYING.value

    def _is_stopped(self):
        return self._state() == States.STOPPED.value

    def _is_ended(self):
        return self._state() == States.ENDED.value

    def _has_error(self):
        return self._state() == States.ERROR

    def _state(self):
        return self._player.get_state()

    def _duration(self):
        return self._player.get_length()

    def _running_time(self):
        return self._player.get_time()
