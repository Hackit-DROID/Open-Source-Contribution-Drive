import os
import sys

import pytest

os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['MAIL_BACKEND'] = 'locmem'
os.environ['NOTIFICATIONS_ASYNC'] = 'false'
os.environ['APP_BASE_URL'] = 'http://testserver'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
from models import db
from notifications import LocmemEmailBackend


@pytest.fixture
def app():
    flask_app.config.update(TESTING=True, MAIL_BACKEND='locmem', NOTIFICATIONS_ASYNC=False,
                            NOTIFICATIONS_ENABLED=True)
    with flask_app.app_context():
        db.create_all()
        LocmemEmailBackend.outbox.clear()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def outbox(app):
    return LocmemEmailBackend.outbox
