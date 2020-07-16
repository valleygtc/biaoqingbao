from flask import Flask

from . import configs


def create_app():
    app = Flask(__name__)
    app.config.from_object(configs)

    from .views import bp_main
    app.register_blueprint(bp_main)

    from .models import db, Image, Group
    db.init_app(app)

    def make_shell_context():
        return dict(db=db, Image=Image, Group=Group)

    app.shell_context_processor(make_shell_context)

    return app
