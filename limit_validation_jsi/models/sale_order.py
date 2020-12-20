# -*- coding: utf-8 -*-

import datetime

from odoo import api, fields, models, _


class saleOrder(models.Model):
    _inherit = "sale.order"

    is_overdue_limit_end = fields.Boolean('Is Overdue?', compute="_compute_remaining_qty")

    @api.depends('partner_id.commercial_partner_id.unreconciled_aml_ids', 'company_id.allowed_overdue_limit_days')
    def _compute_remaining_qty(self):
        for order in self:
            if order.partner_id:
                today = fields.Date.today()
                limit_days = order.company_id.allowed_overdue_limit_days
                date_list = order.partner_id.commercial_partner_id.unreconciled_aml_ids.mapped('date_maturity')
                for date in date_list:
                    if (today - date).days > limit_days:
                        order.is_overdue_limit_end = True
                        break
