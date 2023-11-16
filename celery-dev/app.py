
from appdir import app

if __name__ == '__main__':
    app.start(argv=["-A", "app", "worker", "--loglevel=DEBUG"])
