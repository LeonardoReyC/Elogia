# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Elogia Base",
    'category': 'Extra Tools',
    'summary': """Module Base for the rigth and general behavior""",
    'description': """All the general functionalities will be group in this module""",
    'license': 'AGPL-3',
    'author': "Rapsodoo Iberia",
    'website': "https://www.rapsodoo.com/es/",
    'version': '16.0.1.0.42',
    'depends': [
        'base',
        'base_vat',
        'mail',
        'contacts',
        'account',
        'account_accountant',
        'account_asset',
        'sale',
        'hr',
        'sale_management',
        'account_edi',
        'l10n_mx_edi',
#       'l10n_es_aeat_sii_oca'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/partner_view.xml',
        'views/report_invoice_view.xml',
        'views/product_view.xml'
    ],
    'application': False,
    'assets': {
        'mail.assets_messaging': [
            'elogia_base/static/src/models/*.js',
        ],
    },
}
