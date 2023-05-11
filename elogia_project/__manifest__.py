# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Elogia project",
    'summary': 'Changes to be consider in Elogia enviroment',
    'author': "Rapsodoo Iberia",
    'website': "https://www.rapsodoo.com/es/",
    'category': 'Project/Project',
    'license': 'LGPL-3',
    'version': '16.0.1.0.26',
    'depends': [
        'base',
        'project',
        'calendar',
        'elogia_base',
        'elogia_hr',
        'sale_planning',
        'sale_project',
        'sale_timesheet'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/elogia_view.xml',
        'views/mail_activity_view.xml',
        'views/view_inherit_basic_project_admin.xml',
    ],
    'application': False,
    'assets': {
        'web.assets_backend': [
            'elogia_project/static/src/xml/planning_gantt.xml',
            'elogia_project/static/src/js/backend/planning_gantt_controller.js',
        ],
    }
}
