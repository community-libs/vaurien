"""A simple, flask-based webserver able to control how the proxy behaves"""
from flask import (Flask, request, request_started, request_finished,
                   make_response)
import json

app = Flask(__name__)


@app.route('/handler', methods=['POST', 'GET'])
def update_renderer():
    if request.method == 'POST':
        handler = request.data
        try:
            app.proxy.set_next_handler(handler)
        except KeyError:
            request.errors.add('headers', 'handler',
                               "the '%s' handler does not exist" % handler)
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

    def add(self, location, name=None, description=None):
        """Registers a new error."""
        self.append(dict(
            location=location,
            name=name,
            description=description))


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
