# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_default_type(self):
        env_setting = self.env['setting.type.journal']
        return env_setting.search([('company_id', '=', self.env.company.id),
                                   ('check_default', '=', True),
                                   ('type', '=', 'sale'),
                                   ('type_journal', '=', 'Convencional')], limit=1)

    type_journal_id = fields.Many2one('setting.type.journal', 'Type journal', check_company=True,
                                      default=_get_default_type)
    description = fields.Text('Notes')
    department_id = fields.Many2one('hr.department', 'Department', tracking=1, check_company=True)

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.type_journal_id:
            invoice_vals['journal_id'] = self.type_journal_id.journal_id.id
            invoice_vals['description'] = self.description
        return invoice_vals
