odoo.define('custom_gantt.GanttModel', function (require) {
"use strict";

    var GanttModel = require('web_gantt.GanttModel');


    GanttModel.include({

        _loadGantt: function () {
            var self = this;
            var fields = _.values(this.mapping).concat(this.gantt.to_grouped_by);
            fields.push('display_name');

            if (this.modelName === 'project.task') {
                fields.push('user_name');
                fields.push('task_color');
                fields.push('dependent_task_ids');
            }
            return this._rpc({
                    model: this.modelName,
                    method: 'search_read',
                    context: this.gantt.context,
                    domain: this.gantt.domain.concat(this._focusDomain()),
                    fields: _.uniq(fields),
                })
                .then(function (records) {
                    self.gantt.data = records;
                });
        },
    });

});
