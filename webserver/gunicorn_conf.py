from multiprocessing import cpu_count

bind = 'unix:/tmp/gunicorn.sock'

workers = cpu_count() +1
worker_class = 'uvicorn.workers.UvicornWorker'

loglevel = 'debug'
accessslog = '/users/dorlando/netraiders/access_log'
errorlog = '/users/dorlando/netraiders/error_log'
