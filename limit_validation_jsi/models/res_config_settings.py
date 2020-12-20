# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    allowed_overdue_limit_days = fields.Float('Allowed Days for Overdue')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_overdue_limit = fields.Boolean(string="Overdue Limit", config_parameter='limit_validation_jsi.use_overdue_limit')
    allowed_overdue_limit_days = fields.Float(string="Allowed Days for Overdue", related='company_id.allowed_overdue_limit_days', readonly=False)

    @api.onchange('use_overdue_limit')
    def _onchange_use_overdue_limit(self):
        if not self.use_overdue_limit:
            self.allowed_overdue_limit_days = 0.0
