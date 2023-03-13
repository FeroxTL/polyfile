import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
bind = '{{ settings.GUNICORN_BIND }}'
accesslog = '-'
wsgi_app = 'polyfile.app.wsgi'
reload = False
