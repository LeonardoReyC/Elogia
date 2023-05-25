# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class SettingTypeJournal(models.Model):
    _name = "setting.type.journal"
    _description = "Setting Type Journal"

    name = fields.Char('Name', index=True, default='/')
    type_journal = fields.Selection([
        ('Convencional', 'Convencional'),
        ('Intercompany', 'Intercompany'),
    ], string='Journal type', default='Convencional', index=True, required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True, check_company=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
    check_default = fields.Boolean('Default')
    type = fields.Selection(related='journal_id.type', store=True)

    _sql_constraints = [
        ('journal_type_unique', 'unique (type_journal, journal_id)',
         'This journal already has a related type journal!')
    ]

    @api.constrains('type_journal', 'company_id')
    def check_type_journal(self):
        for record in self:
            if record.type_journal:
                record.name = record.type_journal + '-' + record.company_id.name


class PaymentModeClient(models.Model):
    _name = "payment.mode.client"
    _description = "Payment Mode"

    name = fields.Char('Name', index=True, required=True)


class Partner(models.Model):
    _inherit = "res.partner"

    property_account_passive_id = fields.Many2one(
        comodel_name='account.account',
        company_dependent=True,
        string="Account Passive",
        domain="[('deprecated', '=', False), ('company_id', '=', current_company_id)]"
    )
    trade_name = fields.Char('Trade name', index=True)
    third_party = fields.Selection([
        ('vendor', 'Vendors'),
        ('creditor', 'Creditors'),
        ('group', 'Group company'),
        ('company', 'Associated companies'),
        ('employee', 'Employees'),
    ], string='Third party')
    payment_id = fields.Many2one('payment.mode.client', 'Payment mode (Sales)')
    payment_supplier_id = fields.Many2one('payment.mode.client', 'Payment mode (Purchases)')
    company_bank_ids = fields.Many2many(comodel_name='res.partner.bank', compute='_get_company_bank_ids')
    other_bank_id = fields.Many2one('res.partner.bank', 'Bank payments', company_dependent=True)

    def _get_company_bank_ids(self):
        for rec in self:
            rec.company_bank_ids = [(6, 0, self.env.company.bank_ids.mapped('id'))]

    @api.constrains('vat')
    def check_expense_account(self):
        env_partner = self.env['res.partner']
        for record in self:
            if record.vat:
                if record.company_type == 'company' or (record.company_type == 'person' and not record.parent_id):
                    obj_partner = env_partner.search([('id', '!=', record.id), ('vat', '=', record.vat)])
                    if obj_partner:
                        raise UserError(_('There is already a contact with the same VAT: {}.'.format(record.vat)))

    @api.constrains('vat', 'country_id')
    def check_vat(self):
        # The context key 'no_vat_validation' allows you to store/set a VAT number without doing validations.
        # This is for API pushes from external platforms where you have no control over VAT numbers.
        if self.env.context.get('no_vat_validation'):
            return

        for partner in self:
            country = partner.commercial_partner_id.country_id
            if partner.vat and country.check_vat and self._run_vat_test(partner.vat, country, partner.is_company) is False:
                partner_label = _("partner [%s]", partner.name)
                msg = partner._build_vat_error_message(country and country.code.lower() or None, partner.vat,
                                                       partner_label)
                raise ValidationError(msg)

    @api.constrains('category_id')
    def _check_category_id(self):
        for partner in self:
            if partner.category_id:
                partner.followup_reminder_type = 'manual' if any(
                    not category.auto_notify for category in partner.category_id) else 'automatic'


class PartnerCategory(models.Model):
    _inherit = "res.partner.category"

    auto_notify = fields.Boolean(
        string="Follow-up Reports Notify",
        default=True
    )


class Partner(models.Model):
    _inherit = "res.country"

    check_vat = fields.Boolean(string="Validate VAT")
