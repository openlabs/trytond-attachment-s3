# -*- coding: utf-8 -*-
'''
    trytond_attachment_s3

    :copyright: (c) 2012 by Openlabs Technologies & Consulting (P) Ltd.
    :license: GPLv3, see LICENSE for more details
'''
try:
    import hashlib
except ImportError:
    hashlib = None
    import md5
import base64

from boto.s3.key import Key
from boto.s3.connection import S3Connection

from trytond.config import CONFIG
from trytond.transaction import Transaction
from trytond.model import ModelView, ModelSQL


class Attachment(ModelSQL, ModelView):
    """Attachment
    """
    _name = 'ir.attachment'

    def get_data(self, ids, name):
        res = {}
        db_name = Transaction().cursor.dbname
        s3_conn = S3Connection(
            CONFIG['s3_access_key'], CONFIG['s3_secret_key']
        )
        for attachment in self.browse(ids):
            value = False
            if name == 'data_size':
                value = 0
            if attachment.digest:
                filename = attachment.digest
                if attachment.collision:
                    filename = filename + '-' + str(attachment.collision)
                filename = "/".join([db_name, filename])
                bucket = s3_conn.get_bucket(CONFIG.options['data_s3_bucket'])
                if name == 'data_size':
                    key = bucket.get_key(filename)
                    value = key.size
                else:
                    k = Key(bucket)
                    k.key = filename
                    value = base64.encodestring(k.get_contents_as_string())
            res[attachment.id] = value
        return res

    def set_data(self, ids, name, value):
        if value is False or value is None:
            return
        cursor = Transaction().cursor
        db_name = cursor.dbname

        s3_conn = S3Connection(
            CONFIG['s3_access_key'], CONFIG['s3_secret_key']
        )
        bucket = s3_conn.get_bucket(CONFIG.options['data_s3_bucket'])

        data = base64.decodestring(value)
        if hashlib:
            digest = hashlib.md5(data).hexdigest()
        else:
            digest = md5.new(data).hexdigest()
        filename = "/".join([db_name, digest])
        collision = 0
        if bucket.get_key(filename):
            key2 = Key(bucket)
            key2.key = filename
            data2 = key2.get_contents_as_string()
            if data != data2:
                cursor.execute('SELECT DISTINCT(collision) FROM ir_attachment ' \
                        'WHERE digest = %s ' \
                            'AND collision != 0 ' \
                        'ORDER BY collision', (digest,))
                collision2 = 0
                for row in cursor.fetchall():
                    collision2 = row[0]
                    filename = "/".join([
                        db_name, digest + '-' + str(collision2)
                    ])
                    if bucket.get_key(filename):
                        key2 = Key(bucket)
                        key2.key = filename
                        data2 = key2.get_contents_as_string()
                        if data == data2:
                            collision = collision2
                            break
                if collision == 0:
                    collision = collision2 + 1
                    filename = "/".join([
                        db_name, digest + '-' + str(collision)
                    ])
                    key = Key(bucket)
                    key.key = filename
                    key.set_contents_from_string(data)
        else:
            key = Key(bucket)
            key.key = filename
            key.set_contents_from_string(data)
        self.write(ids, {
            'digest': digest,
            'collision': collision,
            })

Attachment()
