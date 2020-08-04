# -*- coding: utf-8 -*-
{
    'name': "payment_vcsweb",

    'summary': """
        VCS Web payment gateway integration
    """,

    'description': """
        Module to allow for ecommerce web sites to use VCS Web for payment processing
    """,
    'author': "Jumping Bean",
    'website': "http://www.jumpingbean.co.za",
    'category': 'Accounting',
    'version': '1.1',
    'license': 'LGPL-3'

    # any module necessary for this one to work correctly
    'depends': ['payment'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/payment_views.xml',
        'views/payment_vcsweb_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
