# -*- coding: utf-8 -*-
"""
    __init__

    :copyright: © 2012-2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from attachment import Attachment


def register():
    "Register models to tryton pool"
    Pool.register(
        Attachment,
        module='attachment_s3', type_='model'
    )
