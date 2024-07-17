from enum import Enum


class States(Enum):
    OPENING = 1
    BUFFERING = 2
    PLAYING = 3
    PAUSED = 4
    STOPPED = 5
    ENDED = 6
    ERROR = 7
