# -*- coding: utf-8 -*-
##############################################################################
#
#    Part of cube48.de. See LICENSE file for full copyright and licensing details.
#
##############################################################################
{
    'name': "Quick Language Selection",

    'summary': """
        Change the language from user preference menu with only one click.""",

    'description': """
        Change the language from user preference menu with only one click.

        1. Adds Quick Language Switcher to the top right-hand User Menu.
        2. Adds Country flags  to the top right-hand User Menu.
        3. Provides 78 country flags.

    """,

    'author': "cube48 AG",
    'website': "https://www.cube48.de",
    'category': 'Tools',
    'version': '14.0',
    'depends': [
        'base',
    ],
    'data': [
        'views/views.xml',
    ],
    'qweb': ['static/src/xml/base.xml'],
    'images': ["static/description/banner.png"],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
