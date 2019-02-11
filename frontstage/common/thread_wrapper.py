import threading


class ThreadWrapper(threading.Thread):
    def __init__(self, function, *args):
        threading.Thread.__init__(self)
        self.function = function
        self.args = args

    def run(self):
        self.function(*self.args)
