from programme.LiveDataController import LiveDataController


class App:
    def __init__(self):
        self.controller = LiveDataController()
        self.controller.run()


if __name__ == '__main__':
    app = App()


