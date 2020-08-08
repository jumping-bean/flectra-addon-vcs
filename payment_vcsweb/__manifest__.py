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
    'version': '1.0',
    'license': 'LGPL-3',
    'data': [
        'views/payment_views.xml',
        'views/payment_vcsweb_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
