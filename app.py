from routes import Router
from handlers import handle_echo, handle_reverse
from server import Server


if __name__ == "__main__":
    app_router = Router()

    app_router.register('ECHO', handle_echo)
    app_router.register('REVERSE', handle_reverse)

    server = Server(
        host='127.0.0.1',
        port=65432,
        router=app_router,
        max_workers=5
    )
    server.start()