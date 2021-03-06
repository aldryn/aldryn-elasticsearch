# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.module_loading import import_string

from aldryn_addons.utils import boolean_ish
from furl import furl


def parse(url, suffix='default'):
    url = furl(url)
    connection = {
        'hosts': [],
        'index': '',
    }
    engine, protocol, platform = None, None, None
    scheme_parts = url.scheme.split('+')
    if len(scheme_parts) == 2:
        engine, protocol = scheme_parts
    elif len(scheme_parts) == 3:
        engine, protocol, platform = scheme_parts
    else:
        error_url = furl(url.url)
        error_url.password = '----'
        raise Exception((
            'The scheme in the elasticsearch url {} is not supported. It must '
            'have a scheme in the form of backend+protocol+platform:// or '
            'backend+protocol://.'
            'Examples: es+https+aws:// es+http://'
        ).format(error_url))
    url.scheme = protocol

    if '*' in url.path.segments[0]:
        # If the index contains the wildcard, replace it with the suffix
        url.path.segments[0] = url.path.segments[0].replace('*', suffix)

    # extract the index name and remove the path from the original url
    index_name = '{}'.format(url.path.segments[0])
    url.path.segments = []
    connection['INDEX'] = index_name

    if platform == 'aws':
        aws_access_key_id = url.username
        aws_secret_key = url.password
        url.username = None
        url.password = None

        connection['hosts'] = [url.url]
        region = url.host.split('.')[1]
        verify_certs = boolean_ish(url.query.params.get('verify_certs', True))
        ConnectionClass = import_string(url.query.params.get(
            'connection_class',
            'elasticsearch.RequestsHttpConnection'
        ))
        Serializer = import_string(url.query.params.get(
            'serializer',
            'elasticsearch.serializer.JSONSerializer'
        ))
        AWS4Auth = import_string(url.query.params.get(
            'aws_auth',
            'aldryn_elasticsearch.auth.AWS4AuthNotUnicode'
        ))
        connection.update({
            'http_auth': AWS4Auth(
                aws_access_key_id,
                aws_secret_key,
                region,
                'es',
            ),
            'use_ssl': protocol == 'https',
            'verify_certs': verify_certs,
            'connection_class': ConnectionClass,
            'serializer': Serializer(),
        })
    else:
        connection['hosts'] = [url.url]
        connection['index'] = index_name
    return connection
