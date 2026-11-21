# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class SportsCourtBooking(models.Model):
    _name = 'sports.court.booking'
    _description = 'Court Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_time desc'

    name = fields.Char(string='Booking Reference', readonly=True, default=lambda self: _('New'))
    court_id = fields.Many2one('sports.court', string='Court', required=True, tracking=True)
    member_id = fields.Many2one('sports.member', string='Member', tracking=True)
    
    # Guest walk-in info
    is_walkin = fields.Boolean(string='Walk-in Guest', default=False)
    guest_name = fields.Char(string='Guest Name')
    guest_phone = fields.Char(string='Guest Phone')

    booking_date = fields.Date(string='Booking Date', required=True, default=fields.Date.context_today)
    start_time = fields.Datetime(string='Start Time', required=True, tracking=True)
    end_time = fields.Datetime(string='End Time', required=True, tracking=True)
    duration = fields.Float(string='Duration (Hours)', default=1.0, readonly=True)

    # Friday Social Play Support
    is_social_play = fields.Boolean(string='Friday Social Play Session', default=False)
    registered_players_count = fields.Integer(string='Registered Players', default=1)
    max_players = fields.Integer(string='Max Capacity', default=1)

    # Financial breakdown
    base_rate = fields.Float(string='Court Rate', compute='_compute_pricing', store=True)
    discount_percent = fields.Float(string='Discount (%)', compute='_compute_pricing', store=True)
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_pricing', store=True)
    court_fee = fields.Float(string='Court Fee', compute='_compute_pricing', store=True)
    tax_amount = fields.Float(string='Tax Amount (18%)', compute='_compute_pricing', store=True)
    total_amount = fields.Float(string='Total Price (₹)', compute='_compute_pricing', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='confirmed', tracking=True)

    payment_state = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('complimentary', 'Complimentary (Gold Tier)')
    ], string='Payment Status', default='unpaid')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].next_by_code('sports.court.booking') or '0001'
            vals['name'] = f"BK-{seq}"
        
        # Enforce 1-hour duration from start_time if end_time not provided
        if vals.get('start_time') and not vals.get('end_time'):
            st = fields.Datetime.from_string(vals['start_time'])
            vals['end_time'] = fields.Datetime.to_string(st + timedelta(hours=1))
        
        booking = super(SportsCourtBooking, self).create(vals)
        booking._validate_booking_rules()
        return booking

    @api.constrains('start_time', 'end_time', 'court_id', 'state', 'is_social_play')
    def _validate_booking_rules(self):
        for rec in self:
            if rec.state == 'cancelled':
                continue

            # 1. Slot alignment (30-min intervals)
            st = fields.Datetime.from_string(rec.start_time)
            et = fields.Datetime.from_string(rec.end_time)
            if st.minute not in (0, 30):
                raise ValidationError(_("Sessions must start on 30-minute intervals (e.g. 18:00 or 18:30)."))

            # 2. Member daily limit: 'each member can play at most twice a day'
            if rec.member_id:
                same_day_count = self.search_count([
                    ('id', '!=', rec.id),
                    ('member_id', '=', rec.member_id.id),
                    ('booking_date', '=', rec.booking_date),
                    ('state', '!=', 'cancelled')
                ])
                if same_day_count >= 2:
                    raise ValidationError(_("Daily limit reached: Member '%s' can play at most twice a day.") % rec.member_id.name)

            # 3. Anti-collision constraint: 'two people must never end up on the same court at the same time'
            overlap_domain = [
                ('id', '!=', rec.id),
                ('court_id', '=', rec.court_id.id),
                ('state', '!=', 'cancelled'),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time)
            ]
            overlapping = self.search(overlap_domain)

            if rec.is_social_play:
                # Friday Social play allows multiple players on the same court session up to 8
                social_session = overlapping.filtered(lambda b: b.is_social_play)
                if overlapping and not social_session:
                    raise ValidationError(_("Court conflict: An individual booking blocks this time on %s.") % rec.court_id.name)
            else:
                if overlapping:
                    conflict = overlapping[0]
                    raise ValidationError(_("Court Conflict! %s is already booked from %s to %s.") % (
                        rec.court_id.name, conflict.start_time, conflict.end_time
                    ))

    @api.depends('court_id', 'member_id', 'is_walkin')
    def _compute_pricing(self):
        for rec in self:
            rate = rec.court_id.hourly_rate or 800.0
            rec.base_rate = rate
            
            disc_pct = 0.0
            if rec.member_id:
                disc_pct = rec.member_id.court_discount
            
            rec.discount_percent = disc_pct
            disc_amt = round(rate * (disc_pct / 100.0), 2)
            rec.discount_amount = disc_amt
            net_fee = rate - disc_amt
            rec.court_fee = net_fee

            tax = round(net_fee * 0.18, 2) if net_fee > 0 else 0.0
            rec.tax_amount = tax
            rec.total_amount = net_fee + tax
            rec.payment_state = 'complimentary' if rec.total_amount == 0 else 'unpaid'
