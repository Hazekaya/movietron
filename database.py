import json
import os


def _create_file():
    if not os.path.exists('movietron.json'):
        data = {
            "root_path": None,
            "archive_path": None,
            "movies": [],
            "watched_movies": [],
            "current_movie": None,
            "current_movie_time": None,
            "whammies": 1
        }

        json_obj = json.dumps(data, indent=4)

        with open("movietron.json", "w") as outfile:
            outfile.write(json_obj)


class Database:
    def __init__(self):
        _create_file()

    def set_root_path(self, path):
        self._update_data(
            "root_path",
            path
        )

    def get_root_path(self):
        return self._get_data("root_path")

    def set_archive_path(self, path):
        self._update_data("archive_path", path)

    def get_archive_path(self):
        return self._get_data("archive_path")

    def set_current_movie(self, movie_path, time):
        self._update_data(
            "current_movie",
            movie_path,
            "current_movie_time",
            time
        )

    def get_current_movie(self):
        return self._get_data("current_movie")

    def set_movies(self, movie_paths):
        movie_titles = []
        for movie_path in movie_paths:
            title = os.path.basename(movie_path)
            if not self._movie_exists(title):
                movie_titles.append(title)

        self._update_data("movies", movie_titles)

    def get_movies(self):
        return self._get_data("movies")

    def set_watched_movies(self, movie_path):
        title = os.path.basename(movie_path)
        data = self._get_data("watched_movies")
        data.append(title)
        self._update_data("watched_movies", data)

    def get_whammies(self):
        return self._get_data("whammies")

    def set_whammies(self, amount):
        data = (self._get_data("whammies") + amount)
        self._update_data("whammies", data)

    def _movie_exists(self, movie_title):
        titles = self._get_data("movies")
        return movie_title in titles

    def _get_data(self, term):
        try:
            with open('movietron.json', 'r') as infile:
                data = json.load(infile)

            return data[term]

        except FileNotFoundError:
            print('file not found')

        except json.JSONDecodeError:
            print('json fucked up')

    def _update_data(self, term, value, scnd_term=None, scnd_val=None):
        try:
            with open("movietron.json", "r") as infile:
                data = json.load(infile)

            data[term] = value

            if scnd_term and scnd_val and scnd_val > 0:
                data[scnd_term] = scnd_val

            with open("movietron.json", "w") as outfile:
                json.dump(data, outfile, indent=4)

        except FileNotFoundError:
            print("Error: movietron.json file not found")

        except json.JSONDecodeError:
            print("Error: movietron.json file seems to be corrupted")
