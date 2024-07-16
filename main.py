import os
import random
import shutil
import sys
from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from database import Database


def _path_exists(path):
    return os.path.exists(path)


class MovieTron(QMainWindow):
    def __init__(self):
        super(MovieTron, self).__init__()
        self.db = Database()
        self.lbl_welcome = None
        self.lbl_lst_title = None
        self.lst_movies = None
        self.btn_movietron_active = None
        self.menubar = None
        self.statusbar = None

        self.initialize()
        self._movietron()

    def initialize(self):
        self.resize(791, 600)
        self.setWindowTitle("MovieTron")

        self.lbl_welcome = QtWidgets.QLabel(self)
        self.lbl_welcome.setObjectName("lbl_welcome")
        self.lbl_welcome.setText("Let jesus decide what you watch next!")
        self.lbl_welcome.setGeometry(QtCore.QRect(190, 20, 451, 41))

        self.lbl_lst_title = QtWidgets.QLabel(self)
        self.setObjectName("lbl_list_title")
        self.lbl_lst_title.setText("Movies")
        self.lbl_lst_title.setGeometry(QtCore.QRect(310, 110, 181, 16))

        self.lst_movies = QtWidgets.QListWidget(self)
        self.lst_movies.setGeometry(QtCore.QRect(170, 180, 256, 192))

        self.btn_movietron_active = QtWidgets.QPushButton(self)
        self.btn_movietron_active.setText("Let the lord decide!")
        self.btn_movietron_active.setGeometry(QtCore.QRect(320, 420, 161, 61))
        self.btn_movietron_active.setObjectName("btn_pick_movie")
        self.btn_movietron_active.clicked.connect(self._movietron)

        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QtCore.QRect(0, 0, 791, 21))
        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self._set_styles()

    def _movietron(self, time=0):
        root = self.db.get_root_path()
        if root and _path_exists(root):
            movie = self._random_movie()
            self.db.set_current_movie(movie, time)
            print("Movie tron activating")
        else:
            dialog = QtWidgets.QFileDialog().getExistingDirectory(self, "Select Directory")
            path = str(dialog)
            if _path_exists(path):
                self.db.set_root_path(path)

    def end_movie(self, movie):
        archive_path = self.db.get_archive_path()
        if archive_path and _path_exists(archive_path):
            print("copying to archive path")
            self._archive_movie(movie)

        if self._movie_ended():
            self.db.set_watched_movies(movie)
            self.db.set_current_movie(None, 0)
        else:
            self.db.set_current_movie(movie, time=2)

    def use_whammy(self):
        price = -1
        whammies = self.db.get_whammies()
        if whammies > 0:
            self._movietron()
            self.db.set_whammies(price)

    def _random_movie(self):
        movie_paths = self._find_movies()
        extensions = [".mkv", ".mp4", "avi"]

        for file in os.listdir(random.choice(movie_paths)):
            for extension in extensions:
                if file.lower().endswith(extension):
                    return file

    def _find_movies(self):
        root_path = self.db.get_root_path()
        movie_paths = []

        if _path_exists(root_path):
            for path in Path(root_path).iterdir():
                movie_paths.append(str(path))

            return movie_paths

    def _movie_ended(self):
        duration = 10
        time = 5
        return time >= duration

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

    def _set_styles(self):

        self.setStyleSheet(
            "background: solid black;"
        )

        self.lbl_welcome.setStyleSheet(
            "font: 8pt \"Fixedsys\";\n"
            "color: rgb(255, 255, 255);\n"
            "margin: auto;\n"
            "width: 50%;\n"
            "padding: 10px;"
        )

        self.lbl_lst_title.setStyleSheet(
            "font: 8pt \"Fixedsys\";\n"
            "color: rgb(255, 255, 255);\n"
            "margin: auto;\n"
            "width: 50%;\n"
            "padding: 10px;"
        )

        self.lst_movies.setStyleSheet(
            "color: white;"
        )

        self.btn_movietron_active.setStyleSheet(
            "background: solid white;"
        )


def window():
    app = QApplication(sys.argv)
    win = MovieTron()
    win.show()
    sys.exit(app.exec_())


window()
