"""A simple, flask-based webserver able to control how the proxy behaves"""
import os
import json

try:
    from flask import (Flask, request, request_started, request_finished,
                       make_response)
except ImportError as e:
    reqs = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'web-requirements.txt')

    raise ImportError('You need some dependencies to run the web interface. '\
                    + 'You can do so by using "pip install -r '
                    + '%s"\nInitial error: %s' % (reqs, str(e)))

app = Flask(__name__)


@app.route('/handler', methods=['POST', 'GET'])
def update_renderer():
    if request.method == 'POST':
        handler = request.data
        try:
            app.proxy.set_next_handler(handler)
        except KeyError:
            request.errors.add('request', 'handler',
                           'the "%s" handler does not exist.' % handler +
                           ' Use one of the handlers defined in "handlers"',
                           handlers=app.proxy.handlers.keys())
        return "ok"
    else:
        return app.proxy.get_next_handler()


@app.route('/handlers')
def list_handlers():
    """List all the available handlers"""
    resp = make_response(json.dumps({'handlers': app.proxy.handlers.keys()}))
    resp.content_type = 'application/json'
    return resp


# utils

class Errors(list):
    """Holds Request errors
    """
    def __init__(self, status=400):
        self.status = status
        super(Errors, self).__init__()

    def add(self, location, name=None, description=None, **kw):
        """Registers a new error."""
        self.append(dict(
            location=location,
            name=name,
            description=description,
            **kw))


def add_errors(sender, **extra):
    """Add errors to the request"""
    setattr(request, 'errors', Errors())


def convert_errors(sender, response, **extra):
    """convert errors to json if needed"""
    if len(request.errors) > 0:
        response.data = json.dumps({'status': 'error',
                                    'errors': request.errors})
        response.content_type = 'application/json'
        response.status_code = request.errors.status


request_started.connect(add_errors, app)
request_finished.connect(convert_errors, app)
