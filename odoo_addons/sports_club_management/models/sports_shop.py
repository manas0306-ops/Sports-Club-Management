# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_sports_gear = fields.Boolean(string='Is Sports Club Gear', default=True)
    gear_category = fields.Selection([
        ('racket', 'Rackets'),
        ('ball', 'Balls'),
        ('shoe', 'Footwear'),
        ('apparel', 'Apparel'),
        ('accessory', 'Accessories')
    ], string='Gear Category', default='racket')
    
    # Unified stock indicator
    unified_shelf_stock = fields.Float(string='Shelf Stock Quantity', related='qty_available', readonly=True)
    is_low_shelf_stock = fields.Boolean(string='Low Stock Warning', compute='_compute_low_shelf_stock')
    reorder_threshold = fields.Float(string='Reorder Alert Threshold', default=5.0)

    @api.depends('qty_available', 'reorder_threshold')
    def _compute_low_shelf_stock(self):
        for rec in self:
            rec.is_low_shelf_stock = rec.qty_available <= rec.reorder_threshold

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_channel = fields.Selection([
        ('counter_pos', 'Pro Shop Counter (10 Mins Before Match)'),
        ('online_click_collect', 'Sofa Order (Click & Collect at Club)'),
        ('online_delivery', 'Sofa Order (Home Delivery)')
    ], string='Sales Channel', default='counter_pos', required=True)

    sports_member_id = fields.Many2one('sports.member', string='Club Member')

    @api.onchange('sports_member_id')
    def _onchange_sports_member_id(self):
        if self.sports_member_id and self.sports_member_id.shop_discount > 0:
            for line in self.order_line:
                line.discount = self.sports_member_id.shop_discount
