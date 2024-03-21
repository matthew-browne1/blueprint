import gunicorn
import gevent

worker_class = "gevent"

workers = 4
threads = 2

