import multiprocessing

wsgi_app = 'biaoqingbao:create_app()'
bind = '127.0.0.1:5000'
workers = multiprocessing.cpu_count() * 2 + 1
