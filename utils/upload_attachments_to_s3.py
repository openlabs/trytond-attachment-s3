#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    upload_attachments_to_s3

    Uploads the existing attachments in a data folder to S3

    :copyright: (c) 2012-2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import os
import warnings
from optparse import OptionParser

from boto.s3.connection import S3Connection
from boto.s3.key import Key


def upload(connection, bucket, data_path, database, new_db_name=None):
    """
    :param connection: The Amazon S3 connection
    :param bucket: The name of the bucket to which the data has to be uploaded
    :param data_path: The data_path used by Tryton
    :param database: The name of the database
    :param new_db_name: If the db name on new infrastructure is different.
                        This DB name will be used as prefix instead of the
                        existing db name.
    """
    bucket = connection.get_bucket(bucket)

    if new_db_name is None:
        new_db_name = database

    counter = {
        'ignored': 0,
        'uploaded': 0,
        'directories': 0,
    }
    for dirpath, _dn, filenames in os.walk(os.path.join(data_path, database)):
        counter['directories'] += 1
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)

            if bucket.get_key(filename):
                warnings.warn("Duplicate file. Ignore: %s" % filepath)
                counter['ignored'] += 1
                continue

            s3_object = Key(bucket)
            s3_object.key = "%s/%s" % (new_db_name, filename)
            s3_object.set_contents_from_filename(filepath)

            counter['uploaded'] += 1
            print "[%d]: File %s uploaded to S3" % (
                counter['uploaded'], filename
            )
    print """Operation Completed

    Uploaded Documents: %(uploaded)d
    Ignored Documents: %(ignored)d
    Directories Traversed: %(directories)d
    """ % (counter)

if __name__ == '__main__':
    parser = OptionParser(
        usage="usage: %prog [options]" +
            " access_key secret_key bucket data_path db_name"
    )
    parser.add_option("-n", "--new-db-name", dest="new_db_name",
        help="New database name to prefix to the files", default=None)

    (options, args) = parser.parse_args()

    if not len(args) == 5:
        parser.error("Invalid options")

    connection = S3Connection(*args[:2])
    upload(connection, new_db_name=options.new_db_name, *args[2:])
