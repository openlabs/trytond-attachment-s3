# -*- coding: utf-8 -*-
"""
    attachment

    Send attachments to S3

    :copyright: © 2012-2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""

try:
    import hashlib
except ImportError:
    hashlib = None
    import md5

from boto.s3.key import Key
from boto.s3.connection import S3Connection

from trytond.config import CONFIG
from trytond.transaction import Transaction
from trytond.pool import PoolMeta

__all__ = ['Attachment']
__metaclass__ = PoolMeta


class Attachment:
    "Attachment"
    __name__ = 'ir.attachment'

    def get_data(self, name):
        """
        Get the data from S3 instead of filesystem.
        The filename is built as '<DBNAME>/<FILENAME>' in the given S3 bucket

        :param name: name of field name
        :return: Buffer of the file binary
        """
        s3_conn = S3Connection(
            CONFIG['s3_access_key'], CONFIG['s3_secret_key']
        )
        bucket = s3_conn.get_bucket(CONFIG.options['data_s3_bucket'])

        db_name = Transaction().cursor.dbname
        format_ = Transaction().context.pop(
            '%s.%s' % (self.__name__, name), ''
        )
        value = None
        if name == 'data_size' or format_ == 'size':
            value = 0
        if self.digest:
            filename = self.digest
            if self.collision:
                filename = filename + '-' + str(self.collision)
            filename = "/".join([db_name, filename])
            if name == 'data_size' or format_ == 'size':
                key = bucket.get_key(filename)
                value = key.size
            else:
                k = Key(bucket)
                k.key = filename
                value = buffer(k.get_contents_as_string())
        return value

    @classmethod
    def set_data(cls, attachments, name, value):
        """
        Save the attachment to S3 instead of the filesystem

        :param attachments: List of ir.attachment instances
        :param name: name of the field
        :param value: binary data of the attachment (string)
        """
        s3_conn = S3Connection(
            CONFIG['s3_access_key'], CONFIG['s3_secret_key']
        )
        bucket = s3_conn.get_bucket(CONFIG.options['data_s3_bucket'])

        if value is None:
            return
        cursor = Transaction().cursor
        db_name = cursor.dbname

        if hashlib:
            digest = hashlib.md5(value).hexdigest()
        else:
            digest = md5.new(value).hexdigest()
        filename = "/".join([db_name, digest])
        collision = 0
        if bucket.get_key(filename):
            key2 = Key(bucket)
            key2.key = filename
            data2 = key2.get_contents_as_string()
            if value != data2:
                cursor.execute('SELECT DISTINCT(collision) '
                    'FROM ir_attachment '
                    'WHERE digest = %s '
                        'AND collision != 0 '
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
                        if value == data2:
                            collision = collision2
                            break
                if collision == 0:
                    collision = collision2 + 1
                    filename = "/".join([
                        db_name, digest + '-' + str(collision)
                    ])
                    key = Key(bucket)
                    key.key = filename
                    key.set_contents_from_string(value)
        else:
            key = Key(bucket)
            key.key = filename
            key.set_contents_from_string(value)
        cls.write(attachments, {
            'digest': digest,
            'collision': collision,
        })
