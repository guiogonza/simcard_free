bind = "0.0.0.0:8090"
workers = 1            # 1 proceso para compartir caché en memoria
threads = 12           # más hilos para compensar y manejar concurrencia
timeout = 180
keepalive = 5
loglevel = "info"
preload_app = False

def post_fork(server, worker):
    """Lanza el worker de refresco en el único worker."""
    from app import start_background_refresh
    start_background_refresh()
