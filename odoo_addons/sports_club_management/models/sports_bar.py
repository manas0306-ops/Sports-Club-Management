# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SportsBarTable(models.Model):
    _name = 'sports.bar.table'
    _description = 'Club Bar & Cafeteria Table'

    name = fields.Char(string='Table Number', required=True)
    area = fields.Selection([
        ('main_hall', 'Main Hall'),
        ('terrace', 'Terrace Patio'),
        ('lounge', 'Lounge Area'),
        ('bar_counter', 'Bar Counter')
    ], string='Area', default='main_hall')
    capacity = fields.Integer(string='Capacity', default=4)
    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved')
    ], string='Status', default='available')

    active_tab_id = fields.Many2one('sports.bar.tab', string='Active Tab', compute='_compute_active_tab')

    def _compute_active_tab(self):
        for rec in self:
            tab = self.env['sports.bar.tab'].search([('table_id', '=', rec.id), ('status', '=', 'open')], limit=1)
            rec.active_tab_id = tab
            rec.status = 'occupied' if tab else 'available'

class SportsBarTab(models.Model):
    _name = 'sports.bar.tab'
    _description = 'Bar Running Tab'
    _inherit = ['mail.thread']
    _order = 'opened_at desc'

    name = fields.Char(string='Tab Reference', readonly=True, default=lambda self: _('New'))
    table_id = fields.Many2one('sports.bar.table', string='Table')
    member_id = fields.Many2one('sports.member', string='Member (Auto-Discount)')
    customer_name = fields.Char(string='Customer / Guest Name', required=True)
    
    status = fields.Selection([
        ('open', 'Running Tab (Open)'),
        ('settled', 'Settled & Closed'),
        ('void', 'Void')
    ], string='Tab Status', default='open', tracking=True)

    opened_at = fields.Datetime(string='Opened At', default=fields.Datetime.now)
    closed_at = fields.Datetime(string='Closed At')

    line_ids = fields.One2many('sports.bar.order.line', 'tab_id', string='Order Lines')
    discount_percent = fields.Float(string='Member Discount (%)', compute='_compute_discount', store=True)

    subtotal = fields.Float(string='Subtotal', compute='_compute_totals', store=True)
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_totals', store=True)
    tax_amount = fields.Float(string='F&B GST (5%)', compute='_compute_totals', store=True)
    total_amount = fields.Float(string='Grand Total (₹)', compute='_compute_totals', store=True)

    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI / QR Code')
    ], string='Payment Method')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].next_by_code('sports.bar.tab') or '0001'
            vals['name'] = f"TAB-{seq}"
        return super(SportsBarTab, self).create(vals)

    @api.depends('member_id')
    def _compute_discount(self):
        for rec in self:
            rec.discount_percent = rec.member_id.bar_discount if rec.member_id else 0.0

    @api.depends('line_ids.price_total', 'discount_percent')
    def _compute_totals(self):
        for rec in self:
            gross = sum(rec.line_ids.mapped('price_total'))
            disc = round(gross * (rec.discount_percent / 100.0), 2)
            net = gross - disc
            tax = round(net * 0.05, 2)
            rec.subtotal = gross
            rec.discount_amount = disc
            rec.tax_amount = tax
            rec.total_amount = net + tax

    def action_settle_tab(self):
        for rec in self:
            rec.status = 'settled'
            rec.closed_at = fields.Datetime.now()
            if rec.table_id:
                rec.table_id.status = 'available'

class SportsBarOrderLine(models.Model):
    _name = 'sports.bar.order.line'
    _description = 'Bar Order Line & KOT'

    tab_id = fields.Many2one('sports.bar.tab', string='Bar Tab', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Menu Item', required=True)
    quantity = fields.Float(string='Qty', default=1.0)
    price_unit = fields.Float(string='Unit Price', related='product_id.list_price')
    price_total = fields.Float(string='Total', compute='_compute_price_total', store=True)

    # Kitchen Order Ticket (KOT)
    kot_ticket_ref = fields.Char(string='KOT Ticket #', default='KOT-001')
    kitchen_notes = fields.Char(string='Kitchen Notes (e.g. less ice)')
    kot_status = fields.Selection([
        ('pending', 'Pending Preparation'),
        ('preparing', 'Cooking / Shaking'),
        ('ready', 'Ready for Pickup'),
        ('served', 'Served to Table')
    ], string='Kitchen Status', default='pending')

    @api.depends('quantity', 'price_unit')
    def _compute_price_total(self):
        for rec in self:
            rec.price_total = rec.quantity * rec.price_unit
