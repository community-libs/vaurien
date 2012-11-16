"""A simple, flask-based webserver able to control how the proxy behaves"""
import os
import json

try:
    from flask import (Flask, Blueprint, request, request_started,
                       request_finished, jsonify, current_app)
except ImportError as e:
    reqs = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'web-requirements.txt')

    raise ImportError('You need some dependencies to run the web interface. '
                      'You can do so by using "pip install -r '
                      '%s"\nInitial error: %s' % (reqs, str(e)))

api = Blueprint('api', __name__)


@api.route('/behaviors', methods=['GET'])
def get_behaviors():
    return jsonify(behaviors=current_app.proxy.get_behavior_names())


@api.route('/behavior', methods=['POST', 'GET'])
def update_behavior():
    if request.method == 'POST':
        try:
            data = json.loads(request.data)
            name = data['name']
        except ValueError:
            request.errors.add('body', '',
                               'the value is not a valid json object')
        except KeyError:
            request.errors.add('body', '',
                               'the value should contain a "name" key')
        else:
            try:
                current_app.proxy.set_behavior(**data)
            except KeyError:
                request.errors.add('body', 'name',
                                "the '%s' behavior does not exist" % name)

        if len(request.errors) == 0:
            return jsonify(status='ok')
        else:
            return jsonify(status='error')
    else:
        return jsonify(behavior=current_app.proxy.get_behavior()[1])


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
        response.status_code = request.errors.status
    # as we always answer in json for now...
    response.content_type = 'application/json'


def create_app(debug=False):
    app = Flask(__name__)
    app.register_blueprint(api)

    request_started.connect(add_errors, app)
    request_finished.connect(convert_errors, app)

    if debug:
        app.debug = True
    return app

app = create_app()
