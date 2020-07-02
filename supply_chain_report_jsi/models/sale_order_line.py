# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import safe_eval


class saleOrderLine(models.Model):
    _inherit = "sale.order.line"

    remaining_qty = fields.Float('Remaining Qty', compute="_compute_remaining_qty", store="True")
    cost_total = fields.Float('Total Cost', compute="_compute_costing", store="True")
    sales_total = fields.Float('Total Sales', compute="_compute_costing", store="True")
    profit_loss = fields.Float('Profit / Loss', compute="_compute_costing", store="True")
    margin_new = fields.Float('Margin', compute="_compute_costing", store="True")

    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_remaining_qty(self):
        for line in self:
            line.remaining_qty = line.product_uom_qty - line.qty_delivered

    @api.depends('price_subtotal', 'purchase_price', 'remaining_qty')
    def _compute_costing(self):
        for line in self:
            # cost_total
            line.cost_total = line.purchase_price * line.remaining_qty
            # cost_total
            line.sales_total = line.price_unit * line.remaining_qty
            # profit_loss
            line.profit_loss = line.sales_total - line.cost_total
            # margin_new
            if line.price_subtotal:
                line.margin_new = line.profit_loss / line.price_subtotal

    @api.multi
    def open_supply_chain_report(self):
        [action] = self.env.ref('supply_chain_report_jsi.action_stock_move_supply_chain_report_jsi').read()
        action['context'] = dict(safe_eval(action.get('context')), active_id=self.product_id.id, search_default_product_id=self.product_id.id)
        return action
