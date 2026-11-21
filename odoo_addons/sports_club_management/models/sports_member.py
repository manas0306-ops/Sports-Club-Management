# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class SportsMember(models.Model):
    _name = 'sports.member'
    _description = 'Sports Club Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    member_code = fields.Char(string='Member ID', readonly=True, copy=False, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Related Partner', ondelete='cascade')
    
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone', required=True)
    date_of_birth = fields.Date(string='Date of Birth')
    is_junior = fields.Boolean(string='Junior Member (<18)', compute='_compute_is_junior', store=True)
    
    tier = fields.Selection([
        ('gold', 'Gold Tier (Premium Full Access)'),
        ('silver', 'Silver Tier (Standard)'),
        ('junior', 'Junior Tier (Under 18 Discounted)'),
        ('walkin', 'Walk-in Guest')
    ], string='Membership Plan', default='silver', required=True, tracking=True)

    status = fields.Selection([
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended')
    ], string='Status', compute='_compute_status', store=True, tracking=True)

    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    expiry_date = fields.Date(string='Expiry Date', required=True)
    days_to_expiry = fields.Integer(string='Days to Expiry', compute='_compute_status')

    # Entitlements
    court_discount = fields.Float(string='Court Discount (%)', compute='_compute_privileges')
    shop_discount = fields.Float(string='Shop Discount (%)', compute='_compute_privileges')
    bar_discount = fields.Float(string='Bar Discount (%)', compute='_compute_privileges')

    # Club History
    booking_ids = fields.One2many('sports.court.booking', 'member_id', string='Court Bookings')
    bar_tab_ids = fields.One2many('sports.bar.tab', 'member_id', string='Bar Tabs')
    total_spend = fields.Float(string='Total Lifetime Spend', compute='_compute_total_spend')

    emergency_contact = fields.Char(string='Emergency Contact Name')
    emergency_phone = fields.Char(string='Emergency Contact Phone')
    notes = fields.Text(string='Internal Notes')

    @api.model
    def create(self, vals):
        if vals.get('member_code', _('New')) == _('New'):
            tier_prefix = (vals.get('tier', 'sil')[:3]).upper()
            seq = self.env['ir.sequence'].next_by_code('sports.member.code') or '0001'
            vals['member_code'] = f"TC-{tier_prefix}-{seq}"
        return super(SportsMember, self).create(vals)

    @api.depends('date_of_birth')
    def _compute_is_junior(self):
        today = date.today()
        for rec in self:
            if rec.date_of_birth:
                age = (today - rec.date_of_birth).days // 365
                rec.is_junior = age < 18
            else:
                rec.is_junior = rec.tier == 'junior'

    @api.depends('expiry_date')
    def _compute_status(self):
        today = date.today()
        for rec in self:
            if not rec.expiry_date:
                rec.status = 'active'
                rec.days_to_expiry = 999
                continue
            delta = (rec.expiry_date - today).days
            rec.days_to_expiry = delta
            if delta < 0:
                rec.status = 'expired'
            elif delta <= 30:
                rec.status = 'expiring_soon'
            else:
                rec.status = 'active'

    @api.depends('tier')
    def _compute_privileges(self):
        for rec in self:
            if rec.tier == 'gold':
                rec.court_discount = 100.0  # 100% Free
                rec.shop_discount = 20.0   # 20% Off
                rec.bar_discount = 20.0    # 20% Off
            elif rec.tier == 'silver':
                rec.court_discount = 50.0  # 50% Off
                rec.shop_discount = 10.0   # 10% Off
                rec.bar_discount = 10.0    # 10% Off
            elif rec.tier == 'junior':
                rec.court_discount = 60.0  # 60% Off
                rec.shop_discount = 10.0   # 10% Off
                rec.bar_discount = 5.0     # 5% Off
            else:
                rec.court_discount = 0.0
                rec.shop_discount = 0.0
                rec.bar_discount = 0.0

    @api.depends('booking_ids', 'bar_tab_ids')
    def _compute_total_spend(self):
        for rec in self:
            b_total = sum(rec.booking_ids.mapped('total_amount'))
            t_total = sum(rec.bar_tab_ids.filtered(lambda t: t.status == 'settled').mapped('total_amount'))
            rec.total_spend = b_total + t_total

    def action_renew_membership(self):
        for rec in self:
            curr = max(rec.expiry_date or date.today(), date.today())
            rec.expiry_date = curr + timedelta(days=365)
            rec.message_post(body=_("Membership renewed for 1 Year until %s") % rec.expiry_date)
