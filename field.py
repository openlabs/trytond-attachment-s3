# -*- coding: utf-8 -*-
"""
    field

    Add S3Binary field which automatically sends the file to S3 instead of
    storing in filesystem

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import logging

from boto.s3.key import Key
from boto.exception import S3ResponseError
from boto.s3.connection import S3Connection
from trytond.model import fields
from trytond.config import CONFIG
from trytond.transaction import Transaction


class S3Binary(fields.Function):
    """
    Define a binary field which stores data in Amazon S3
    instead of File System.

    The arguments of the field are same as that of :class:~fields.Binary

    The S3 configuration is reused by the field.

    .. tip::

        This module need not be installed in the tryton database to use
        this field. Just importing this field type will do.

    example::

        from trytond.modules.trytond_attchment_s3.field import S3Binary

        class Model(ModelSQL):
            __name__ = "test.model"

            filename = fields.Char('Filename')
            image = S3Binary("String", filename='filename')
    """
    _type = 'binary'

    def __init__(self, *args, **kwargs):
        super(S3Binary, self).__init__(fields.Binary(*args, **kwargs), None)
        self._field.readonly = False

    @classmethod
    def get_bucket(cls):
        '''
        Return an S3 bucket for the current instance
        '''
        s3_conn = S3Connection(
            CONFIG['s3_access_key'], CONFIG['s3_secret_key']
        )
        return s3_conn.get_bucket(CONFIG['data_s3_bucket'])

    @classmethod
    def get_filename(cls, model, record_id):
        '''
        Construct a filename for the given model, record and database

        The constructed file name is 'db_name/model.name/id'

        This method could be optionally subclassed to change the file name
        creation. For example if you want to make a cloud front distribution
        of the bucket and want to use a different approach to creating the
        file.

        :param model: Model object
        :param record_id: Integer ID of the record
        :return: Constructed filename as a string
        '''
        db_name = Transaction().cursor.dbname
        return "/".join([db_name, model._name, str(record_id)])

    @classmethod
    def get(cls, ids, model, name, values=None):
        '''
        Get the File from Amazon S3

        :param ids: List of integer ids of records
        :param model: Model object
        :param name: Name passed to function field
        :param values: Apparently unused
        :return: a dictionary with ids as key and values as value
        '''
        result = {}

        bucket = cls.get_bucket()

        for record in model.browse(ids):
            filename = cls.get_filename(model, record.id)
            if name == 'data_size':
                try:
                    key = bucket.get_key(filename)
                    value = key.size
                except S3ResponseError, exc:
                    logging.error(exc)
                    value = 0
            else:
                try:
                    key = Key(bucket)
                    key.key = filename
                    value = buffer(key.get_contents_as_string())
                except S3ResponseError, exc:
                    logging.error(exc)
                    value = None
            result[record.id] = value
        return result

    @classmethod
    def set(cls, ids, model, name, value):
        '''
        Store the file to Amazon S3

        :param ids: A list of ids.
        :param model: The model.
        :param name: The name of the field.
        :param value: The value to set.
        '''
        if not value:
            return

        bucket = cls.get_bucket()
        for id_ in ids:
            key = Key(bucket)
            key.key = cls.get_filename(model, id_)
            key.set_contents_from_string(value)
