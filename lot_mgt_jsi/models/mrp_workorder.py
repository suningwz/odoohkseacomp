# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round


class MrpProduction(models.Model):
    _inherit = 'mrp.workorder'

    @api.depends('current_quality_check_id', 'qty_producing')
    def _compute_component_id(self):
        for wo in self.filtered(lambda w: w.state not in ('done', 'cancel')):
            if wo.current_quality_check_id.point_id:
                wo.component_id = wo.current_quality_check_id.point_id.component_id
                wo.test_type = wo.current_quality_check_id.point_id.test_type
            elif wo.current_quality_check_id.component_id:
                wo.component_id = wo.current_quality_check_id.component_id
                wo.test_type = 'register_consumed_materials'
            else:
                wo.test_type = ''
            if wo.test_type == 'register_consumed_materials' and wo.quality_state == 'none':
                if wo.current_quality_check_id.component_is_byproduct:
                    moves = wo.production_id.move_finished_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == wo.component_id)
                else:
                    moves = wo.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_id == wo.component_id)
                move = moves[:1]
                lines = wo.active_move_line_ids.filtered(lambda l: l.move_id in moves)
                completed_lines = lines.filtered(lambda l: l.lot_id) if wo.component_tracking != 'none' else lines
                wo.component_remaining_qty = float_round(sum(moves.mapped('unit_factor')) * wo.qty_producing - sum(completed_lines.mapped('qty_done')), precision_rounding=move.product_uom.rounding)
                wo.component_uom_id = move.product_uom
            # Code for Add lot from related move lines
            if wo.component_id:
                move = wo.move_line_ids.filtered(lambda x: x.product_id == wo.component_id)
                if move:
                    wo['lot_id'] = move[0].lot_id.id
