import requests
import urlparse


def change_handler(handler, host=None, credentials=None):
    """Change the handler by sending an HTTP request to the vaurien HTTP server

    :param handler: the handler to use. It should be compatible with what's
                    defined in your vaurien configuration.
    :param host: the host to use. Default value is localhost:8080
    :param credentials: Optional credential parameters. They should be provided
                        as a tuple of (login, password). Default value is no
                        credentials.

    In case the call fails, return a (resp, handlers) tuple containing the
    response andd the list of acceptable handlers.
    """

    if not host:
        host = 'http://localhost:8000'

    kwargs = {}
    if credentials is not None:
        kwargs['auth'] = credentials

    resp = requests.post(urlparse.urljoin(host, '/handler'), data=handler,
                         headers={'content-type': 'application/json'},
                         **kwargs)

    # in case the request failed, display the list of available handlers.
    handlers = []
    if resp.status_code != 200:
        if 'errors' in resp.json \
            and resp.json['errors'] \
            and 'handlers' in resp.json['errors'][0]:
            handlers = resp.json['errors'][0]['handlers']
    return resp, handlers


def main():
    """Command-line tool to change the handler that's being used by vaurien"""
    import argparse
    parser = argparse.ArgumentParser(description='Change the vaurien handler')
    parser.add_argument(dest='handler',
                        help='The vaurien handler to set for the next calls')
    parser.add_argument('--host', dest='host', default='http://localhost:8080',
                        help='The host to use. Provide the scheme.')
    parser.add_argument('--credentials', dest='credentials', default=None)

    args = parser.parse_args()
    resp, handlers = change_handler(args.handler, args.host, args.credentials)
    if resp.status_code != 200:
        print 'The request failed with status %s. Please use one of %s' % (
            resp.status_code, ', '.join(handlers))
    else:
        print 'Handler changed to "%s"' % args.handler
