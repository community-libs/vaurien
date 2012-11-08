"""A simple, flask-based webserver able to control how the proxy behaves"""
import os
import json

try:
    from flask import (Flask, request, request_started, request_finished,
                       jsonify)
except ImportError as e:
    reqs = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'web-requirements.txt')

    raise ImportError('You need some dependencies to run the web interface. '
                      'You can do so by using "pip install -r '
                      '%s"\nInitial error: %s' % (reqs, str(e)))

app = Flask(__name__)


@app.route('/handlers', methods=['GET'])
def get_handlers():
    return jsonify(handlers=app.proxy.get_handler_names())


@app.route('/handler', methods=['POST', 'GET'])
def update_renderer():
    if request.method == 'POST':
        data = json.loads(request.data)
        name = data['name']
        try:
            app.proxy.set_handler(**data)
        except KeyError:
            request.errors.add('headers', 'handler',
                               "the '%s' handler does not exist" % name)
        return "ok"
    else:
        return app.proxy.get_handler()[1]


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
