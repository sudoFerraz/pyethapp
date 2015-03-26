from hashlib import md5
import os
from devp2p.service import BaseService
import gevent
import leveldb
from pyethereum import compress
from pyethereum import slogging
from pyethereum.slogging import get_logger

slogging.set_level('db', 'debug')
log = slogging.get_logger('db')


class LevelDB(BaseService):
    """A service providing an interface to a level db."""

    name = 'db'

    def __init__(self, app):
        super(LevelDB, self).__init__(app)
        self.dbfile = os.path.join(app.config['app']['dir'], app.config['db']['path'])

    def _run(self):
        log.info('opening LevelDB', path=self.dbfile)
        self.db = leveldb.LevelDB(self.dbfile)
        self.uncommitted = dict()
        while True:
            gevent.sleep(0)

    def stop(self):
        # commit?
        log.info('closing db')

    def get(self, key):
        log.debug('getting entry', key=key)
        if key in self.uncommitted:
            if self.uncommitted[key] is None:
                raise KeyError("key not in db")
            return self.uncommitted[key]
        o = compress.decompress(self.db.Get(key))
        self.uncommitted[key] = o
        return o

    def put(self, key, value):
        log.debug('putting entry', key=key, value=value)
        self.uncommitted[key] = value

    def commit(self):
        log.debug('committing', db=self)
        batch = leveldb.WriteBatch()
        for k, v in self.uncommitted.items():
            if v is None:
                batch.Delete(k)
            else:
                batch.Put(k, compress.compress(v))
        self.db.Write(batch, sync=False)
        self.uncommitted.clear()

    def delete(self, key):
        log.debug('deleting entry', key=key)
        self.uncommitted[key] = None

    def _has_key(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def __contains__(self, key):
        return self._has_key(key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.db == other.db

    def __repr__(self):
        return '<DB at %d uncommitted=%d>' % (id(self.db), len(self.uncommitted))
