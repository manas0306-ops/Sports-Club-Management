# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SportsCorporateInvoice(models.Model):
    _inherit = 'account.move'

    sports_client_type = fields.Selection([
        ('individual_dues', 'Member Annual Dues'),
        ('corporate_club', 'Corporate Client (e.g. IT Firm Sports Club)'),
        ('tournament_rental', 'Tournament Facility Rental')
    ], string='Sports Invoice Type', default='individual_dues')

class SportsLeaveApproval(models.Model):
    _inherit = 'hr.leave'

    department_shift_covered = fields.Boolean(
        string='Court / Bar Shift Covered',
        help='Indicates whether replacement staff is scheduled for court or bar shifts during this leave.'
    )
