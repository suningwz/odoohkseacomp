# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Stock Demand Update-jsi",
    'summary': """
        Stock Demand Update""",
    'description': """
        Allow user to update Initial demands from its related MO.
    """,
    'version': '0.1',
    'author': "jsi-odoo",
    'depends': ['mrp', 'stock'],
    'data': [
        'views/stock_views.xml',
    ],
}
