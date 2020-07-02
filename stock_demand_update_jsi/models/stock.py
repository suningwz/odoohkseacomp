# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_update_demand(self):
        self.ensure_one()
        for line in self.move_ids_without_package:
            if len(line.move_dest_ids) == 1:
                line.product_uom_qty = line.move_dest_ids.product_uom_qty