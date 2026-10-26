$from app.main import app\n\nfor route in app.routes:\n    print(route.path, route.methods)
