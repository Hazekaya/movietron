import math
import os
import queue
import random
import shutil
import sys
import threading
from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from database import Database
from mediaplayer import MediaPlayer
import ffmpeg


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


def _path_exists(path):
    return os.path.exists(path)


def _base_name(path):
    return os.path.basename(path)


def _archive_movie(movie_path):
    for filename in os.listdir(movie_path):
        file_path = os.path.join(movie_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


class MovieTron(QMainWindow):
    def __init__(self):
        super(MovieTron, self).__init__()
        self.db = Database()
        self.player = MediaPlayer(self)
        self.lst_movies = None
        self._btn_select_dir = None
        self._btn_boot_movietron = None
        self._btn_movietron_active = None
        self._whammy_count = None
        self._movie_watched_count = None
        self._lbl_movie_title = None
        self._lbl_whammies = None
        self._lbl_movie_count = None
        self.err_dialog = None
        self._selected_movie = None
        self._initialize()
        self._initialize_data()

    def _select_dir(self):
        default_path = os.path.expanduser("~\\Downloads")
        dialog = QtWidgets.QFileDialog()
        dialog.setDirectory(default_path)
        dialog = QtWidgets.QFileDialog().getExistingDirectory(self, "Select root directory")
        path = str(dialog)
        if _path_exists(path):
            self.db.set_root_path(path)
            self._initialize_data()

    def _boot_movietron(self):
        if self.db.get_root_path() and _path_exists(self.db.get_root_path()):
            if self.db.get_current_movie() is None or self.db.get_whammies() > 0:
                movie = self._random_movie()
                self._selected_movie = movie

                if self.db.get_current_movie():
                    self.use_whammy()
        else:
            self._show_error("Select a root directory first")

    def _movietron_activate(self, time=0):
        if self._selected_movie:
            current_movie_time = self.db.get_current_movie_time()
            movie = self._selected_movie

            result_queue = queue.Queue()
            self._get_movie_data(movie, result_queue)

            duration_ms = result_queue.get()

            if movie:
                if current_movie_time and current_movie_time > 0:
                    self.player.start(movie, current_movie_time, self.db.get_current_movie_duration())
                else:
                    self.db.set_current_movie(self._selected_movie, time)
                    self.db.set_current_movie_duration(duration_ms)
                    self.player.start(self._selected_movie)
        else:
            self._show_error("Roll for a movie first.")

    def _show_error(self, message):
        self.err_dialog.showMessage(message)

    def _initialize_data(self):
        if self.db.get_root_path() and _path_exists(self.db.get_root_path()):
            movie_paths = self._find_movies()
            self._fill_movie_list(movie_paths)

            current_movie = self.db.get_current_movie()
            if current_movie and _path_exists(current_movie):
                self._selected_movie = self.db.get_current_movie()

        self._whammy_count.display(self.db.get_whammies())
        self._movie_watched_count.display(self.db.get_movie_count())

    def end_movie(self, movie_path, duration=0):
        archive_path = self.db.get_archive_path()
        if archive_path and _path_exists(archive_path):
            _archive_movie(movie_path)
        if duration == 0:
            self.db.set_watched_movies(movie_path)
            self.db.set_current_movie(None, None)
            self.db.set_current_movie_duration(None)
            self.db.set_movie_count(1)
        else:
            self.db.set_current_movie(movie_path, duration)

    def use_whammy(self):
        price = -1
        self.db.set_whammies(price)

    def _random_movie(self):
        movie_paths = self._find_movies()
        extensions = [".mkv", ".mp4", "avi"]
        random_path = self._selected_movie
        if not self._selected_movie:
            random_path = random.choice(movie_paths)

        if os.path.exists(random_path):
            print(random_path)

        for file in os.listdir(random_path):
            print(file)
            for extension in extensions:
                if file.lower().endswith(extension):
                    full_path = os.path.join(random_path, file)
                    return full_path

    def _has_current_movie(self):
        current_movie = self.db.get_current_movie()
        return current_movie

    def _update_whammies(self):
        print("updating whammies")

    def _fill_movie_list(self, movie_paths):
        for movie_path in movie_paths:
            movie = os.path.basename(movie_path)
            item = QtWidgets.QListWidgetItem()
            item.setText(movie)
            self.lst_movies.addItem(item)

    def _on_list_item_clicked(self, item):
        movie = item.text()
        self._set_movie(movie)

    def _find_movies(self):
        root_path = self.db.get_root_path()
        movie_paths = []

        if _path_exists(root_path):
            for path in Path(root_path).iterdir():
                movie_paths.append(str(path))

        return movie_paths

    def _set_movie(self, path):
        print(f"path: {path}")
        self._selected_movie = f"{self.db.get_root_path()}\\{path}"
        self._selected_movie = self._random_movie()
        name = _base_name(path.rsplit("\\", 1)[0])
        self._lbl_movie_title.setText(name)

    @threaded
    def _get_movie_data(self, movie_path, result_queue):
        video_streams = [stream for stream in ffmpeg.probe(movie_path)["streams"] if stream["codec_type"] == "video"]
        duration_s = float(video_streams[0]['duration'])
        duration_ms = int(math.floor(duration_s * 1000))
        result_queue.put(duration_ms)

    def _initialize(self):
        self.resize(800, 600)
        self.setWindowTitle("MovieTron")

        self.lst_movies = QtWidgets.QListWidget(self)
        self.lst_movies.setGeometry(QtCore.QRect(30, 20, 300, 560))

        self._movie_watched_count = QtWidgets.QLCDNumber(self)
        self._movie_watched_count.setGeometry(QtCore.QRect(710, 20, 64, 20))

        self._whammy_count = QtWidgets.QLCDNumber(self)
        self._whammy_count.setGeometry(QtCore.QRect(710, 70, 64, 20))

        self._lbl_movie_count = QtWidgets.QLabel(self)
        self._lbl_movie_count.setGeometry(QtCore.QRect(620, 20, 91, 20))
        self._lbl_movie_count.setText("Movies watched: ")

        self._lbl_whammies = QtWidgets.QLabel(self)
        self._lbl_whammies.setGeometry(QtCore.QRect(620, 70, 100, 20))
        self._lbl_whammies.setText("Whammies: ")

        self._btn_select_dir = QtWidgets.QPushButton(self)
        self._btn_select_dir.setGeometry(QtCore.QRect(350, 20, 120, 40))
        self._btn_select_dir.setText("Select root directory")

        self._btn_boot_movietron = QtWidgets.QPushButton(self)
        self._btn_boot_movietron.setGeometry(QtCore.QRect(340, 540, 120, 40))
        self._btn_boot_movietron.setText("Roll for movie")

        self._btn_movietron_active = QtWidgets.QPushButton(self)
        self._btn_movietron_active.setGeometry(QtCore.QRect(470, 540, 120, 40))
        self._btn_movietron_active.setText("Activate Movietron")

        self._lbl_movie_title = QtWidgets.QLabel(self)
        self._lbl_movie_title.setGeometry(350, 190, 200, 20)

        self._btn_select_dir.clicked.connect(self._select_dir)
        self._btn_boot_movietron.clicked.connect(self._boot_movietron)
        self._btn_movietron_active.clicked.connect(self._movietron_activate)
        self.lst_movies.itemClicked.connect(self._on_list_item_clicked)

        self.err_dialog = QtWidgets.QErrorMessage()

        self._set_styles()

    def _set_styles(self):

        self.setStyleSheet(
            "background: solid #121212;"
        )

        self.lst_movies.setStyleSheet(
            "color:white;\n"
            "background:transparent;"
        )

        self._lbl_movie_count.setStyleSheet(
            "color:white"
        )

        self._lbl_whammies.setStyleSheet(
            "color:white"
        )

        self._btn_select_dir.setStyleSheet(
            "color: #E6FDFF;\n"
            "background: #39838A;\n"
            "padding: 10px;\n"
            "border-radius:25px"
        )

        self._btn_boot_movietron.setStyleSheet(
            "color: #E6FDFF;\n"
            "background: #39838A;\n"
            "padding: 10px;\n"
            "border-radius:25px"
        )

        self._btn_movietron_active.setStyleSheet(
            "color: #E6FDFF;\n"
            "background: #39838A;\n"
            "padding: 10px;\n"
            "border-radius:25px"
        )

        self._lbl_movie_title.setStyleSheet(
            "color:white"
        )


def window():
    app = QApplication(sys.argv)
    win = MovieTron()
    win.show()
    sys.exit(app.exec_())


window()
