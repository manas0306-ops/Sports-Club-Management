# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SportsTrialBooking(models.Model):
    _name = 'sports.trial.booking'
    _description = 'Visitor Free Trial Session'
    _inherit = ['mail.thread']

    name = fields.Char(string='Trial Ref', readonly=True, default=lambda self: _('New'))
    visitor_name = fields.Char(string='Visitor Full Name', required=True)
    visitor_email = fields.Char(string='Email', required=True)
    visitor_phone = fields.Char(string='Phone', required=True)
    
    sport_type = fields.Selection([
        ('tennis', 'Tennis Trial'),
        ('cricket', 'Cricket Net Trial'),
        ('padel', 'Padel Trial')
    ], string='Sport', default='tennis', required=True)

    trial_date = fields.Date(string='Trial Date', required=True)
    time_slot = fields.Char(string='Time Slot', default='10:00 - 11:00 AM')
    assigned_coach = fields.Many2one('hr.employee', string='Assigned Coach')
    
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('converted', 'Converted to Member'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', tracking=True)

    lead_id = fields.Many2one('crm.lead', string='Originating Lead / Enquiry')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].next_by_code('sports.trial.booking') or '0001'
            vals['name'] = f"TRL-{seq}"
        return super(SportsTrialBooking, self).create(vals)

    def action_convert_to_member(self):
        self.ensure_one()
        member_vals = {
            'name': self.visitor_name,
            'email': self.visitor_email,
            'phone': self.visitor_phone,
            'tier': 'silver',
            'start_date': fields.Date.context_today(self),
            'expiry_date': fields.Date.add(fields.Date.context_today(self), years=1),
            'notes': _("Converted from Trial Session %s") % self.name
        }
        member = self.env['sports.member'].create(member_vals)
        self.state = 'converted'
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Member Profile'),
            'res_model': 'sports.member',
            'res_id': member.id,
            'view_mode': 'form',
            'target': 'current',
        }
