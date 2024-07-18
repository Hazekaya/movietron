import os
import random
import shutil
import sys
from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from database import Database
from mediaplayer import MediaPlayer


def _path_exists(path):
    return os.path.exists(path)


def _base_name(path):
    return os.path.basename(path)


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

        self.initialize()
        self._initialize_data()

    def initialize(self):
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

        self._set_styles()

    def _select_dir(self):
        dialog = QtWidgets.QFileDialog().getExistingDirectory(self, "Select root directory")
        path = str(dialog)
        if _path_exists(path):
            self.db.set_root_path(path)
            self._initialize_data()

    def _boot_movietron(self):
        if self.db.get_root_path() and _path_exists(self.db.get_root_path()):
            self._selected_movie = self._random_movie()
        else:
            self._select_dir()

    def _initialize_data(self):
        if self.db.get_root_path() and _path_exists(self.db.get_root_path()):
            movie_paths = self._find_movies()
            self._fill_movie_list(movie_paths)
        else:
            print("No path, no movies")

    def _movietron_activate(self, time=0):
        if self._selected_movie:
            self.db.set_current_movie(self._selected_movie, time)
            self.player.start(self._selected_movie)

    def end_movie(self, movie_path, duration=0):
        archive_path = self.db.get_archive_path()
        if archive_path and _path_exists(archive_path):
            self._archive_movie(movie_path)
        print(f"duration: {duration}")
        if duration == 0:
            self.db.set_watched_movies(movie_path)
            self.db.set_current_movie(None, None)
        else:
            self.db.set_current_movie(movie_path, duration)

    def use_whammy(self):
        price = -1
        self.db.set_whammies(price)

    def _random_movie(self):
        movie_paths = self._find_movies()
        extensions = [".mkv", ".mp4", "avi"]

        random_path = random.choice(movie_paths)
        for file in os.listdir(random_path):
            for extension in extensions:
                if file.lower().endswith(extension):
                    full_path = os.path.join(random_path, file)
                    return full_path

    def _archive_movie(self, movie_path):
        for filename in os.listdir(movie_path):
            file_path = os.path.join(movie_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

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

    def _random_movie(self):
        movie_paths = self._find_movies()
        extensions = [".mkv", ".mp4", "avi"]

        random_path = random.choice(movie_paths)
        for file in os.listdir(random_path):
            for extension in extensions:
                if file.lower().endswith(extension):
                    full_path = os.path.join(random_path, file)
                    self._set_movie(full_path)
                    return full_path

    def _set_movie(self, path):
        name = _base_name(path.rsplit("\\", 1)[0])
        self._lbl_movie_title.setText(name)

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
