# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from calendar import monthrange
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CopyMonthWizard(models.TransientModel):
    _name = 'copy.month.wizard'
    _description = 'Copy Month Wizard'

    name = fields.Char('Name', index=True, default='/')
    slot_ids = fields.Many2many('planning.slot', 'copy_planning_rel', 'copy_id', 'slot_id', string='Planning slot')
    start_datetime = fields.Datetime('Start date')
    end_datetime = fields.Datetime('End date')
    more_info = fields.Text('Error info.')

    def check_any_value(self, list_error):
        value_slot_ids = [item['item'].id for item in list_error]
        return value_slot_ids

    def remove_slot(self, slot, list_ok):
        if slot.id in list_ok:
            list_ok.remove(slot.id)

    def check_create_slot(self, view_slot, init_date, end_date, view_slot_origin):
        slot_filters = False
        slot_errors = ''
        list_ok = []
        list_error = []
        val_errors = ''
        env_leave = self.env['hr.leave'].search([('state', 'not in', ['draft', 'refuse']),
                                                 ('date_from', '>=', init_date), ('date_to', '<=', end_date)])
        for slot in view_slot:
            next_month = slot.end_datetime.date() + relativedelta(months=1)
            leave_filter = env_leave.filtered(lambda e: e.date_from.date() <= next_month <= e.date_to.date())
            slot_filter_duple = view_slot_origin.filtered(lambda e: e.end_datetime.date() == next_month)
            list_ok.append(slot.id)
            if slot_filter_duple:
                if slot.id not in self.check_any_value(list_error):
                    list_error.append({'error': 'duplicity', 'item': slot})
                self.remove_slot(slot, list_ok)
            if any(employee for employee in leave_filter.mapped('employee_ids') if leave_filter and employee == slot.employee_id):
                if slot.id not in self.check_any_value(list_error):
                    list_error.append({'error': 'time', 'item': slot})
                self.remove_slot(slot, list_ok)
            if slot.project_id:
                contact = slot.employee_id.work_contact_id
                if contact.id not in slot.project_id.message_follower_ids.mapped('partner_id').ids:
                    if slot.id not in self.check_any_value(list_error):
                        list_error.append({'error': 'not_project', 'item': slot})
                    self.remove_slot(slot, list_ok)
                if slot.project_id.date and slot.project_id.date < next_month:
                    if slot.id not in self.check_any_value(list_error):
                        list_error.append({'error': 'not_project_date', 'item': slot})
                    self.remove_slot(slot, list_ok)
        if list_ok:
            slot_filters = view_slot.filtered(lambda e: e.id in list_ok)
        for item in list_error:
            if item['error'] == 'not_contract':
                for i in item['item']:
                    val_errors += '[{}:{}] - {} does not have an associated contract. \n' \
                        .format(i.start_datetime.date(), i.end_datetime.date(), i.employee_id.name)
            if item['error'] == 'contract_valid':
                for i in item['item']:
                    val_errors += '[{}:{}] - Its required that the contract associated with ' \
                                  'the employee {} is not Expired or Cancelled.\n' \
                        .format(i.start_datetime.date(), i.end_datetime.date(), i.employee_id.name)
            if item['error'] == 'date_init':
                for i in item['item']:
                    val_errors += '[{}:{}] - The employee/resource {} should not be working in this period. ' \
                                  'Check the start date of the Contract.\n' \
                        .format(i.start_datetime.date(), i.end_datetime.date(), i.employee_id.name)
            if item['error'] == 'date_end':
                for i in item['item']:
                    val_errors += '[{}:{}] - The employee/resource {} should not be working in this period. ' \
                                  'Check end date of the Contract.\n' \
                        .format(i.start_datetime.date(), i.end_datetime.date(), i.employee_id.name)
            if item['error'] == 'duplicity':
                for i in item['item']:
                    val_errors += '[{}:{}] - There are planning for {} at the same time.\n' \
                        .format(i.start_datetime.date(), i.end_datetime.date(), i.employee_id.name)
            if item['error'] == 'duplicity':
                for i in item['item']:
                    val_errors += '[{}:{}] - {} has requested time off in this period.\n' \
                        .format(i.start_datetime.date(), i.end_datetime.date(), i.employee_id.name)
            if item['error'] == 'not_project':
                for i in item['item']:
                    val_errors += '[{}:{}] - {} cannot have planning on project {}.\n' \
                        .format(i.start_datetime.date(), i.end_datetime.date(), i.employee_id.name,
                                i.project_id.name)
            if item['error'] == 'not_project_date':
                for i in item['item']:
                    val_errors += '[{}:{}] - Expiration date of the project {} is {}.\n' \
                        .format(i.start_datetime.date(), i.end_datetime.date(), i.project_id.name,
                                i.project_id.date)
        slot_errors = val_errors
        return slot_filters, slot_errors

    @api.onchange('start_datetime', 'end_datetime', 'slot_ids')
    def onchange_dates(self):
        env_planning = self.env['planning.slot']
        init_date = self.start_datetime
        end_date = self.end_datetime
        if (init_date or end_date) and not self.slot_ids:
            view_slot_origin = env_planning.search([('start_datetime', '>=', init_date),
                                                    ('end_datetime', '<=', end_date),
                                                    ('recurrency_id', '=', False), ('was_copied', '=', False)])
            view_slot = env_planning.search([('start_datetime', '>=', init_date - relativedelta(months=1)),
                                             ('end_datetime', '<=', end_date - relativedelta(months=1)),
                                             ('recurrency_id', '=', False), ('was_copied', '=', False)])
            if view_slot:
                slot_filters = self.check_create_slot(view_slot, init_date, end_date, view_slot_origin)
                self.slot_ids = slot_filters[0]
                self.more_info = slot_filters[1]

    def action_copy_previous_month(self):
        new_slot_values = []
        slots_to_copy = self.slot_ids
        for slot in slots_to_copy:
            if not slot.was_copied:
                values = slot.copy_data()[0]
                if values.get('start_datetime'):
                    values['start_datetime'] += relativedelta(months=1)
                if values.get('end_datetime'):
                    values['end_datetime'] += relativedelta(months=1)
                new_slot_values.append(values)
        if new_slot_values:
            slots_to_copy.write({'was_copied': True})
            self.slot_ids.with_context({'wizard_origin': 'wizard'}).create(new_slot_values)
            return True
        return False


class Project(models.Model):
    _inherit = "project.project"

    department_id = fields.Many2one('hr.department', 'Department', check_company=True)

    @api.constrains('allow_billable')
    def check_allow_billable_project(self):
        for record in self:
            if record.allow_billable:
                record.allow_billable = False


class Task(models.Model):
    _inherit = "project.task"

    action_user_id = fields.Many2one('res.users', string="Action required by", help='Action required by any user',
                                     tracking=1)

    @api.constrains('timesheet_ids', 'parent_id')
    def _check_subtask(self):
        for record in self:
            if record.parent_id:
                if not record.project_id:
                    record.project_id = record.parent_id.project_id.id
                if not record.display_project_id:
                    record.display_project_id = record.parent_id.project_id.id
                if not record.partner_id:
                    record.partner_id = record.parent_id.partner_id.id
                if record.timesheet_ids:
                    raise UserError(_('You cannot charge hours into a child task. Contact with an Administrator.'))
            if any(item for item in record.timesheet_ids if not item.employee_id.hourly_cost):
                raise UserError(_('You cannot charge hours because the Employee does not have a Cost. '
                                  'Contact with an Administrator.'))

    @api.model
    def create(self, vals_list):
        res = super(Task, self).create(vals_list)
        if res.parent_id:
            if not res.project_id:
                res.project_id = res.parent_id.project_id.id
            if not res.display_project_id:
                res.display_project_id = res.parent_id.project_id.id
            if not res.partner_id:
                res.partner_id = res.parent_id.partner_id.id
            if res.partner_id:
                res.message_unsubscribe(partner_ids=res.partner_id.ids)
        return res

    def write(self, vals):
        if self.user_has_groups('project.group_project_user'):
            if self.user_has_groups('!project.group_project_manager'):
                if 'project_id' in vals or 'partner_id' in vals or 'company_id' in vals or 'analytic_account_id' in vals:
                    raise UserError(_('You do not have permission to modify fields such as: "Project", "Customer", '
                                      '"Analytical account" and "Company".\n Contact an administrator.'))
        return super(Task, self).write(vals)


class Planning(models.Model):
    _inherit = 'planning.slot'

    role_id = fields.Many2one('planning.role', string="Hub", compute="_compute_role_id", store=True, readonly=False,
                              copy=True, group_expand='_read_group_role_id')
    hours_available = fields.Float('Hours available')
    total_hours = fields.Float('Total Hours')

    @api.constrains('resource_id', 'project_id')
    def check_value_in_models(self):
        for record in self:
            if not record.resource_id:
                raise UserError(_('Resource field is required.'))
            if not record.project_id:
                raise UserError(_('Project field is required.'))

    @api.constrains('employee_id', 'employee_id.contract_id', 'overlap_slot_count', 'allocated_hours', 'start_datetime',
                    'end_datetime', 'project_id', 'project_id.date')
    def _check_employee_amount(self):
        for record in self:
            env_slot = self.env['planning.slot'].search([('resource_id', '=', record.resource_id.id),
                                                         ('id', '!=', record.id)])
            total_hours_by_combine = record._get_slot_duration()
            calendar_combine = record.employee_id.resource_calendar_id or record.company_id.resource_calendar_id
            first_day = record.start_datetime.replace(day=1)
            daysInMonth = monthrange(first_day.year, first_day.month)[1]
            last_day = record.start_datetime.replace(day=daysInMonth)
            if calendar_combine:
                total_hours_by_combine = calendar_combine.get_work_hours_count(first_day, last_day, compute_leaves=True)
            record.total_hours = total_hours_by_combine
            record.hours_available = record.total_hours - record.allocated_hours
            slot_filter = env_slot.filtered(lambda e: e.start_datetime.month == first_day.month)
            val_available = record.total_hours - sum(slot_filter.mapped('allocated_hours'))
            record.hours_available = val_available if slot_filter else val_available
            if 'wizard_origin' not in self._context:
                if record.employee_id:
                    if record.overlap_slot_count:
                        raise UserError(_('There are {} planning for this resource at the same time.'
                                          .format(record.overlap_slot_count)))
                    if record.is_absent:
                        raise UserError(_('{} has requested time off in this period.'
                                          .format(record.employee_id.name)))
                    if record.project_id:
                        contact = record.employee_id.work_contact_id
                        if contact:
                            if contact.id not in record.project_id.message_follower_ids.mapped('partner_id').ids:
                                raise UserError(_('{} cannot have planning on this project.'
                                                  .format(record.employee_id.name)))
                        else:
                            raise UserError(_('Employee {} have not related contact.'
                                              .format(record.employee_id.name)))
                        if record.project_id.date:
                            if record.project_id.date < record.end_datetime.date():
                                raise UserError(_('The expiration date of the project is {}.'
                                                  .format(record.project_id.date)))
                        else:
                            raise UserError(_('The project have not expiration date.'))


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    department_account_id = fields.Many2one('hr.department', 'Department')
    type_note = fields.Selection([
        ('man', 'Manual'),
        ('aut', 'Automatic'),
    ], string='Type note', default='man')
    product_analytic_id = fields.Many2one('product.product', 'Product analytic')
    employee_contact_id = fields.Many2one('res.partner', 'Contact employee', tracking=1,
                                          domain="[('employee', '=', True)]")

    @api.constrains('unit_amount', 'employee_id', 'date')
    def _check_unit_amount(self):
        env_line = self.env['account.analytic.line']
        for record in self:
            if record.unit_amount and record.employee_id.resource_calendar_id and record.date:
                date_from = datetime.combine(record.date, time.min)
                date_to = datetime.combine(record.date, time.max)
                hours = record.employee_id.resource_calendar_id.get_work_hours_count(date_from, date_to, True)
                if record.unit_amount > hours:
                    raise UserError(_("The maximum limit for this timesheet must not exceed %s hours per day.")
                                    % hours)
                else:
                    obj_line = env_line.search([('date', '=', record.date),
                                                ('employee_id', '=', record.employee_id.id),
                                                ('company_id', '=', self.env.company.id),
                                                ('id', '!=', record.id)])
                    if obj_line:
                        if sum(obj_line.mapped('unit_amount'), record.unit_amount) > hours:
                            raise UserError(_("The maximum limit for this timesheet must not exceed %s hours per day.")
                                            % hours)

    @api.constrains('account_id', 'move_line_id', 'product_id', 'is_timesheet')
    def check_analytic_id(self):
        for record in self:
            record.type_note = 'man'
            if record.account_id:
                record.department_account_id = record.account_id.department_id.id
                if record.move_line_id.employee_id:
                    record.employee_contact_id = record.move_line_id.employee_id.id
            if record.move_line_id or record.is_timesheet:
                record.type_note = 'aut'
            if record.product_id:
                record.product_analytic_id = record.product_id.id

    @staticmethod
    def verify_working_days(plan_date, employee=False):
        """" Funtion to define how many working hours has the employee day.
            Exist two options:
            1- The planning doesnt have employee(only employee_level). In this case the hours will be static
                - Weekend = 0 hours
                - Weekdays = 8 hours
            2- The planning has employee. In this case the standard function from resources get_work_hours_count()
            will be called to get the number
            Return: Number of working hours
        """
        # If day week is from Monday to Friday return 8 hours
        hours = 8
        if fields.Date.to_date(plan_date).weekday() in [5, 6]:
            # If day week is Saturday or Sunday return 0 hours
            hours = 0
        if not employee:
            # If not employee the values will be statics
            return hours
        else:
            # If exist employee
            # We always verify day by day how many working hours are
            # date_from = datetime.combine(plan_date.date(), time.min)
            date_from = datetime.combine(plan_date, time.min)
            date_to = datetime.combine(plan_date, time.max)
            # date_to = datetime.combine(plan_date.date(), time.max)
            if employee.resource_calendar_id:
                # Call function from resource calendar to get the number of working hours in the period
                hours = employee.resource_calendar_id.get_work_hours_count(date_from, date_to, True)
            return hours
