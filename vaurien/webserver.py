from cornice.service import Service
from pyramid.config import Configurator
from pyramid.events import NewRequest

behavior = Service('behavior', path='/behavior')
behaviors = Service('behaviors', path='/behaviors')


@behavior.put()
def set_behavior(request):
    try:
        data = request.json
        name = data['name']
    except ValueError:
        request.errors.add('body', '',
                           'the value is not a valid json object')
    except KeyError:
        request.errors.add('body', '',
                           'the value should contain a "name" key')
    else:
        try:
            request.proxy.set_behavior(**data)
        except KeyError:
            request.errors.add('body', 'name',
                               "the '%s' behavior does not exist" % name)
    return {'status': 'ok'}


@behavior.get()
def get_behavior(request):
    return {'behavior': request.proxy.get_behavior()[1]}


@behaviors.get()
def get_behaviors(request):
    return {'behaviors': request.proxy.get_behavior_names()}


def add_proxy_to_request(event):
    event.request.proxy = event.request.registry['proxy']


def get_config(global_config=None, **settings):
    if global_config is None:
        global_config = {}
    config = Configurator(settings=settings)
    config.include('cornice')
    config.scan('vaurien.webserver')

    config.add_subscriber(add_proxy_to_request, NewRequest)
    return config
