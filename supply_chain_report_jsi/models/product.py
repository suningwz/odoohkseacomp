# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import safe_eval


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def open_supply_chain_report(self):
        [action] = self.env.ref('supply_chain_report_jsi.action_stock_move_supply_chain_report_jsi').read()
        action['context'] = dict(safe_eval(action.get('context')), active_id=self.id, search_default_product_id=self.id)
        return action
