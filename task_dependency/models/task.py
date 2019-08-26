# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class Task(models.Model):
    _inherit = 'project.task'

    starting_date = fields.Date(string='Start Date',required=True,default=fields.Date.context_today)
    expected_duration = fields.Integer(default=1, required=True)
    expected_completion = fields.Date(compute="get_expected_completion",store=True,readonly=True)
    dependent_task_ids = fields.Many2many('project.task', relation='rel_project_task_project_task', column1='child_task_id', column2='parent_task_id')

    @api.depends('expected_duration','starting_date')
    def get_expected_completion(self):
        for rec in self:
            rec.expected_completion = rec.starting_date + relativedelta(days=rec.expected_duration)


    @api.model
    def create(self, vals):

        res = super(Task,self).create(vals)

        if res.dependent_task_ids:
            dates = [task.expected_completion for  task in res.dependent_task_ids if task.expected_completion]
            if dates:
                new_start_date = max(dates)
                if new_start_date != res.starting_date:
                    res.starting_date = new_start_date

        return res

    @api.multi
    def write(self,vals):
        if vals.get('expected_duration',0) < 0:
            raise UserError('Cannot have a negative duration!')

        res = super(Task,self).write(vals)

        if 'dependent_task_ids' in vals:
            for rec in self:
                if rec.dependent_task_ids:
                    dates = [task.expected_completion for  task in rec.dependent_task_ids if task.expected_completion]
                    if dates:
                        new_start_date = max(dates)
                        if new_start_date != rec.starting_date:
                            rec.starting_date = new_start_date

        if 'starting_date' in vals or 'expected_duration' in vals:
            for rec in self:
                parents = rec.get_parents(rec)
                for p in parents:
                    dates = [task.expected_completion for task in p.dependent_task_ids if task.expected_completion]
                    if dates:
                        p.starting_date = max(dates)

        return res

    @api.onchange('dependent_task_ids')
    def onchange_dependent_task_completion(self):
        dates = [task.expected_completion for  task in self.dependent_task_ids if task.expected_completion]
        if dates:
            new_start_date = max(dates)
            if new_start_date != self.starting_date:
                self.starting_date = new_start_date

    @api.multi
    def get_parents(self,task):
        parents = self.env['project.task'].search([('dependent_task_ids', 'in', [task.id])])
        return parents

    @api.constrains('dependent_task_ids')
    def no_circular_dependecy(self):
        for rec in self:
            #get all parent tasks
            parent_tasks = rec
            children_tasks = self.env['project.task']
            parents = rec.get_parents(rec)
            while parents:
                next_parents = self.env['project.task']
                for p in parents:
                    if p in parent_tasks:
                        raise UserError('Cannot add circular dependencies between tasks!')
                    next_parents |= p.get_parents(p) or self.env['project.task']
                parent_tasks |= parents
                parents = next_parents

            children = rec.dependent_task_ids
            while children:
                next_children = self.env['project.task']
                for c in children:
                    if c in children_tasks:
                        raise UserError('Cannot add circular dependencies between tasks!')
                    next_children |= c.dependent_task_ids
                children_tasks |= children
                children = next_children


            if parent_tasks and children_tasks and any([c in parent_tasks for c in children_tasks]):
                raise UserError('Cannot add circular dependencies between tasks!')



