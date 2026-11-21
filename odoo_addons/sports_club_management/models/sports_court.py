# -*- coding: utf-8 -*-
from odoo import models, fields

class SportsCourt(models.Model):
    _name = 'sports.court'
    _description = 'Sports Club Court & Pitch'
    _order = 'sequence, name'

    name = fields.Char(string='Court Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    sport_type = fields.Selection([
        ('tennis', 'Tennis Court'),
        ('cricket', 'Cricket Pitch/Net'),
        ('padel', 'Padel Court'),
        ('badminton', 'Badminton Court')
    ], string='Sport Type', default='tennis', required=True)

    surface_type = fields.Selection([
        ('clay', 'Red Clay'),
        ('synthetic_turf', 'Synthetic Turf'),
        ('hard', 'Hard Court (Plexicushion)'),
        ('grass', 'Natural Turf')
    ], string='Surface Type', default='clay')

    has_floodlights = fields.Boolean(string='Floodlights Enabled', default=True)
    hourly_rate = fields.Float(string='Standard Hourly Rate (₹)', default=800.0, required=True)
    is_active = fields.Boolean(string='Active', default=True)
    booking_ids = fields.One2many('sports.court.booking', 'court_id', string='Bookings')
