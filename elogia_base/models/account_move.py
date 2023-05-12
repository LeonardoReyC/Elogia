# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    employee_id = fields.Many2one('res.partner', string='Employee', tracking=1, domain="[('employee', '=', True)]")


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_mode_id = fields.Many2one('payment.mode.client', 'Payment mode (Sales)', tracking=1)
    payment_supplier_id = fields.Many2one('payment.mode.client', 'Payment mode (Purchase)', tracking=1)
    category_id = fields.Many2many(related="partner_id.category_id", string='Partner tags')
    description = fields.Text('Notes')
    ref_previous = fields.Char('Other reference')
    fiscal_folio = fields.Char(string='Folio Fiscal', related='l10n_mx_edi_cfdi_uuid')

    @api.constrains('partner_id', 'move_type')
    def check_payment_id(self):
        for record in self:
            if record.partner_id:
                if record.move_type in ['out_invoice', 'out_refund']:
                    record.payment_mode_id = record.partner_id.payment_id.id
                    if record.partner_id.other_bank_id:
                        record.partner_bank_id = record.partner_id.other_bank_id.id
                if record.move_type in ['in_invoice', 'in_refund']:
                    record.payment_supplier_id = record.partner_id.payment_supplier_id.id

    """  def _compute_sii_description(self):
        default_description = self.default_get(["sii_description"])["sii_description"]
        for invoice in self:
            description = ""
            if invoice.move_type in ["out_invoice", "out_refund"]:
                description = invoice.company_id.sii_header_customer or ""
            elif invoice.move_type in ["in_invoice", "in_refund"]:
                description = invoice.company_id.sii_header_supplier or ""
            method = invoice.company_id.sii_description_method
            if method == "fixed":
                description = (description + invoice.company_id.sii_description) or default_description
            elif method == "manual":
                if invoice.sii_description != default_description:
                    # keep current content if not default
                    description = invoice.sii_description
            else:  # auto method
                if invoice.invoice_line_ids:
                    if description:
                        description += " | "
                    names = invoice.mapped("invoice_line_ids.name") or invoice.mapped("invoice_line_ids.ref")
                    description += " - ".join(filter(None, names))
            if description and invoice.company_id:
                if invoice.company_id.sii_header_customer:
                    val_custom = invoice.company_id.sii_header_customer
                    if description.find(val_custom) != -1:
                        description = description.replace(val_custom, val_custom + ' ').strip()
                if invoice.company_id.sii_header_supplier:
                    val_sup = invoice.company_id.sii_header_supplier
                    if description.find(val_sup) != -1:
                        description = description.replace(val_sup, val_sup + ' ').strip()
            invoice.sii_description = (description or "")[:500] or "/" """

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft=True)
        for record in res.filtered(lambda e: e.l10n_mx_edi_post_time is not False):
            record.l10n_mx_edi_post_time = record.l10n_mx_edi_post_time - timedelta(hours=1)
        return res


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    partner_id = fields.Many2one('res.partner', string='Assigned to', tracking=1, domain="[('employee', '=', True)]")


class BankRecWidget(models.Model):
    _inherit = "bank.rec.widget"

    form_employee_id = fields.Many2one('res.partner', string='Employee', domain="[('employee', '=', True)]")


class AccountReconcileModelLine(models.Model):
    _inherit = "account.reconcile.model.line"

    employee_id = fields.Many2one('res.partner', string='Employee', domain="[('employee', '=', True)]")
