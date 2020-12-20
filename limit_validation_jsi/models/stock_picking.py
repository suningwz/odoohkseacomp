# -*- coding: utf-8 -*-

import datetime

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_overdue_limit_end = fields.Boolean('Is Overdue?', compute="_compute_remaining_qty", store="True")

    @api.depends('partner_id.commercial_partner_id.unreconciled_aml_ids.date', 'company_id.allowed_overdue_limit_days')
    def _compute_remaining_qty(self):
        for picking in self:
            if picking.partner_id:
                today = fields.Date.today()
                limit_days = picking.company_id.allowed_overdue_limit_days
                date_list = picking.partner_id.commercial_partner_id.unreconciled_aml_ids.mapped('date_maturity')
                for date in date_list:
                    if (today - date).days > limit_days:
                        picking.is_overdue_limit_end = True
                        break
