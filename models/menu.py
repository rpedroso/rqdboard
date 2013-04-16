# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

response.logo = A(B('plugin_rqdboard example'),
                  _class="brand",
                  _href="http://www.web2py.com/")

response.title = 'Redis Queue Example'
response.subtitle = 'for web2py'

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = ''
response.meta.description = ''
response.meta.keywords = ''
response.meta.generator = ''

response.menu = [
    ('Home', False, URL('default', 'index'), []),
    ('Dashboard', False, URL('default', 'dashboard'), [])
]
