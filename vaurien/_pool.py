from gevent.queue import PriorityQueue, Empty
import time
import contextlib
import sys

# Sentinel used to mark an empty slot in the MCClientPool queue.
# Using sys.maxint as the timestamp ensures that empty slots will always
# sort *after* live connection objects in the queue.
EMPTY_SLOT = sys.maxint, None


class FactoryPool(object):

    def __init__(self, factory, maxsize=200, timeout=60):
        self.factory = factory
        self.maxsize = maxsize
        self.timeout = timeout
        self.clients = PriorityQueue(maxsize)
        # If there is a maxsize, prime the queue with empty slots.
        if maxsize is not None:
            for _ in xrange(maxsize):
                self.clients.put(EMPTY_SLOT)

    @contextlib.contextmanager
    def reserve(self):
        """Context-manager to obtain a Client object from the pool."""
        ts, client = self._checkout_connection()
        try:
            yield client
        finally:
            self._checkin_connection(ts, client)

    def _checkout_connection(self):
        # If there's no maxsize, no need to block waiting for a connection.
        blocking = self.maxsize is not None

        # Loop until we get a non-stale connection, or we create a new one.
        while True:
            try:
                ts, client = self.clients.get(blocking)
            except Empty:
                # No maxsize and no free connections, create a new one.
                # XXX TODO: we should be using a monotonic clock here.
                # see http://www.python.org/dev/peps/pep-0418/
                now = int(time.time())
                return now, self.factory()
            else:
                now = int(time.time())
                # If we got an empty slot placeholder, create a new connection.
                if client is None:
                    return now, self.factory()
                # If the connection is not stale, go ahead and use it.
                if ts + self.timeout > now:
                    return ts, client
                # Otherwise, the connection is stale.
                # Close it, push an empty slot onto the queue, and retry.
                if hasattr(client, 'disconnect'):
                    client.disconnect()

                self.clients.put(EMPTY_SLOT)
                continue

    def _checkin_connection(self, ts, client):
        """Return a connection to the pool."""
        if hasattr(client, '_closed') and client._closed:
            self.clients.put(EMPTY_SLOT)
            return

        # If the connection is now stale, don't return it to the pool.
        # Push an empty slot instead so that it will be refreshed when needed.
        now = int(time.time())
        if ts + self.timeout > now:
            self.clients.put((ts, client))
        else:
            if self.maxsize is not None:
                self.clients.put(EMPTY_SLOT)
