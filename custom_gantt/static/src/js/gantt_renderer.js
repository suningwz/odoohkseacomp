odoo.define('custom_gantt.CustomGanttRenderer', function (require) {
    "use strict";

    var GanttRenderer = require('web_gantt.GanttRenderer');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var time = require('web.time');
    var _lt = core._lt;

    GanttRenderer.include({
        _configGantt: function () {
            var self = this;

            gantt.config.autosize = "y";
            gantt.config.round_dnd_dates = false;
            gantt.config.drag_links = false;
            gantt.config.drag_progress = false;
            gantt.config.drag_resize = true;
            gantt.config.grid_width = 550;
            gantt.config.row_height = 30;
            gantt.config.duration_unit = "day";
            gantt.config.initial_scroll = false;
            gantt.config.preserve_scroll = true;
            gantt.config.columns = [
                {
                    name: "text",
                    label: _lt("Task Name"),
                    tree: true,
                    width: '*',
                    resize: true,
                }, {
                    name: "user",
                    label: _lt("User"),
                    align: "center",
                    width: '150',
                    resize: true,
                }, {
                    name: "duration",
                    label: _lt("Days"),
                    align: "center",
                    width: '75',
                }];
            gantt.templates.grid_folder = function () {
                return "";
            };
            gantt.templates.grid_file = function () {
                return "";
            };
            gantt.templates.grid_indent = function () {
                return "<div class='gantt_tree_indent' style='width:20px;'></div>";
            };
            gantt.config.start_on_monday = moment().startOf("week").day();
            gantt.config.start_date = this.state.start_date;
            gantt.config.end_date = this.state.end_date;

            // dnd by date
            gantt.config.round_dnd_dates = !!this.round_dnd_dates;

            // Set resizing of tasks
            if (this.drag_resize === '0' || this.drag_resize === 'false' || this.edit === 'false') {
                gantt.config.drag_resize = false;
            }

            // Set drag_move of tasks
            gantt.config.drag_move = this.edit ? JSON.parse(this.edit) : true;

            // Configure the duration_unit
            if (this.duration_unit) {
                gantt.config.duration_unit = this.duration_unit;
            }

            // the class of the task bar
            gantt.templates.task_class = function (start, end, task) {
                var classes = ["o_gantt_color" + task.color + "_0"];
                if (self.type === "consolidate" || self.type === "planning") {
                    classes.push('consolidation');
                    if (task.is_group) {
                        classes.push("has_child");
                    } else {
                        classes.push("is_leaf");
                    }
                }
                return classes.join(" ");
            };

            // the class for the rows
            gantt.templates.task_row_class = function (start, end, task) {
                var classes = ["level_" + task.$level];
                return classes;
            };

            // The class for the cells
            gantt.templates.task_cell_class = function (item, date) {
                var classes = "date_" + date.getTime();
                var today = new Date();
                if (self.state.scale !== "year" && (date.getDay() === 0 || date.getDay() === 6)) {
                    classes += " weekend_task";
                }
                if (self.state.scale !== "day" && date.getDate() === today.getDate() && date.getMonth() === today.getMonth() && date.getYear() === today.getYear()) {
                    classes += " today";
                }
                return classes;
            };

            gantt.templates.date_scale = null;

            // Task text format
            var mapping = this.state.mapping;
            gantt.templates.task_text = function (start, end, task) {
                // default
                var text = "";
                // consolidation
                if (self.type === "consolidate" || self.type === "planning") {
                    if (task.is_group) {
                        text = self._consolidationChildren(task);
                    } else if (self.state.fields[mapping.consolidation]) {
                        var field = self.state.fields[mapping.consolidation];
                        var consolidation = field_utils.format[field.type](task.consolidation, field);
                        text = consolidation + "<span class=\"half_opacity\"> " + self.state.fields[mapping.consolidation].string + "</span>";
                    }
                }
                return text;
            };
        },
        _renderGantt: function () {
            var self = this;

            var mapping = this.state.mapping;
            var grouped_by = this.state.to_grouped_by;

            // Prepare the tasks
            var tasks = _.compact(_.map(this.state.data, function (task) {
                task = _.clone(task);

                var task_start = time.auto_str_to_date(task[mapping.date_start]);
                if (!task_start) {
                    return false;
                }

                var task_stop;
                var percent;
                if (task[mapping.date_stop]) {
                    task_stop = time.auto_str_to_date(task[mapping.date_stop]);
                    // If the date_stop is a date, we assume that the whole day should be included.
                    if (self.state.fields[mapping.date_stop].type === 'date') {
                        task_stop.setTime(task_stop.getTime() + 86400000);
                    }
                    if (!task_stop) {
                        task_stop = moment(task_start).clone().add(1, 'hours').toDate();
                    }
                } else {
                    // FIXME this code branch is not tested
                    if (!mapping.date_delay) {
                        return false;
                    }
                    var field = self.state.fields[mapping.date_delay];
                    var tmp = field_utils.format[field.type](task[mapping.date_delay], field);
                    if (!tmp) {
                        return false;
                    }
                    var m_task_start = moment(task_start).add(tmp, gantt.config.duration_unit);
                    task_stop = m_task_start.toDate();
                }

                if (_.isNumber(task[mapping.progress])) {
                    percent = task[mapping.progress] || 0;
                } else {
                    percent = 100;
                }

                task.task_start = task_start;
                task.task_stop = task_stop;
                task.percent = percent;

                // Don't add the task that stops before the min_date
                // Usefull if the field date_stop is not defined in the gantt view
                if (self.min_date && task_stop < new Date(self.min_date)) {
                    return false;
                }

                return task;
            }));

            // get the groups
            var split_groups = function (tasks, grouped_by) {
                if (grouped_by.length === 0) {
                    return tasks;
                }
                var groups = [];
                _.each(tasks, function (task) {
                    var group_name = task[_.first(grouped_by)];
                    var group = _.find(groups, function (group) {
                        return _.isEqual(group.name, group_name);
                    });
                    if (group === undefined) {
                        // Create the group of the other levels
                        group = {name:group_name, tasks: [], __is_group: true,
                                 group_start: false, group_stop: false, percent: [],
                                 open: true};

                        // Add the group_by information for creation
                        group.create = [_.first(grouped_by), task[_.first(grouped_by)]];

                        // folded or not
                        if ((self.fold_last_level && grouped_by.length <= 1) ||
                            self.state.context.fold_all ||
                            self.type === 'planning') {
                            group.open = false;
                        }

                        // the group color
                        // var model = self.state.fields[_.first(grouped_by)].relation;
                        // if (model && _.has(color_by_group, model)) {
                        //     group.consolidation_color = color_by_group[model][group_name[0]];
                        // }

                        groups.push(group);
                    }
                    if (!group.group_start || group.group_start > task.task_start) {
                        group.group_start = task.task_start;
                    }
                    if (!group.group_stop || group.group_stop < task.task_stop) {
                        group.group_stop = task.task_stop;
                    }
                    group.percent.push(task.percent);
                    if (self.open_task_id === task.id && self.type !== 'planning') {
                        group.open = true; // Show the just created task
                    }
                    group.tasks.push(task);
                });
                _.each(groups, function (group) {
                    group.tasks = split_groups(group.tasks, _.rest(grouped_by));
                });
                return groups;
            };
            var groups = split_groups(tasks, grouped_by);

            // If there is no task, add a dummy one
            if (groups.length === 0) {
                groups = [{
                    'id': 0,
                    'display_name': '',
                    'task_start': this.state.focus_date.toDate(),
                    'task_stop': this.state.focus_date.toDate(),
                    'percent': 0,
                }];
            }

            // Creation of the chart
            var gantt_tasks = [];
            var generate_tasks = function (task, level, parent_id) {
                if ((task.__is_group && !task.group_start) || (!task.__is_group && !task.task_start)) {
                    return;
                }
                if (task.__is_group) {
                    // Only add empty group for the first level
                    if (level > 0 && task.tasks.length === 0){
                        return;
                    }

                    var project_id = _.uniqueId("gantt_project_");
                    var field = self.state.fields[grouped_by[level]];
                    var group_name = task[mapping.name] ? field_utils.format[field.type](task[mapping.name], field) : "-";
                    // progress
                    var sum = _.reduce(task.percent, function (acc, num) { return acc+num; }, 0);
                    var progress = sum / task.percent.length / 100 || 0;
                    var t = {
                        'id': project_id,
                        'text': group_name,
                        'user': task.user_id || '',
                        'is_group': true,
                        'start_date': task.group_start || '',
                        'duration': gantt.calculateDuration(task.group_start, task.group_stop),
                        'progress': progress,
                        'create': task.create,
                        'open': task.open,
                        'consolidation_color': task.task_color || 0,
                        'index': gantt_tasks.length,
                    };
                    if (parent_id) { t.parent = parent_id; }
                    gantt_tasks.push(t);
                    _.each(task.tasks, function (subtask) {
                        generate_tasks(subtask, level+1, project_id);
                    });
                }
                else {
                    // Consolidation
                    gantt_tasks.push({
                        'id': "gantt_task_" + task.id,
                        'text': task.display_name || '',
                        'user': task.user_name || '',
                        'active': task.active || true,
                        'start_date': task.task_start || '',
                        'duration': gantt.calculateDuration(task.task_start, task.task_stop),
                        'progress': task.percent / 100,
                        'parent': parent_id || 0,
                        'consolidation': task[mapping.consolidation] || null,
                        'consolidation_exclude': self.consolidation_exclude || null,
                        'color': task.task_color || 0,
                        'index': gantt_tasks.length,
                    });
                }
            };
            _.each(groups, function (group) { generate_tasks(group, 0); });

            this._ganttContainer(gantt_tasks);
            this._configureGanttChart(tasks, grouped_by, gantt_tasks);
        },
    });
});