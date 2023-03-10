# -*- coding: utf-8 -*-
#################################################################################
# Author      : AxisTechnolabs.com
# Copyright(c): 2011-Axistechnolabs.com.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import calendar as cal
import random
import pytz
import uuid
from datetime import datetime, timedelta, time
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from babel.dates import format_datetime

from odoo import api, fields, models, _, Command
from odoo.tools.misc import get_lang
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import ValidationError


class CalendarAppointmentType(models.Model):
    _name = "calendar.appointment.type"
    _description = "Online Appointment Type"
    _inherit = ['mail.thread', "website.seo.metadata", 'website.published.mixin']
    _order = "sequence"

    sequence = fields.Integer('Sequence')
    name = fields.Char('Appointment Type', required=True, translate=True)
    min_schedule_hours = fields.Float('Schedule before (hours)', required=True, default=1.0)
    max_schedule_days = fields.Integer('Schedule not after (days)', required=True, default=15)
    min_cancellation_hours = fields.Float('Cancel Before (hours)', required=True, default=1.0)
    appointment_duration = fields.Float('Appointment Duration', required=True, default=1.0)

    reminder_ids = fields.Many2many('calendar.alarm', string="Reminders")
    location = fields.Char('Location', help="Location of the appointments")
    message_confirmation = fields.Html('Confirmation Message', translate=True)
    message_intro = fields.Html('Introduction Message', translate=True)

    country_ids = fields.Many2many(
        'res.country', 'website_calendar_type_country_rel', string='Restrict Countries',
        help="Keep empty to allow visitors from any country, otherwise you only allow visitors from selected countries")
    question_ids = fields.One2many('calendar.appointment.question', 'appointment_type_id', string='Questions', copy=True)

    slot_ids = fields.One2many('calendar.appointment.slot', 'appointment_type_id', 'Availabilities', copy=True)
    appointment_tz = fields.Selection(
        _tz_get, string='Timezone', required=True, default=lambda self: self.env.user.tz,
        help="Timezone where appointment take place")
    employee_ids = fields.Many2many('hr.employee', 'website_calendar_type_employee_rel',
                                    domain=[('user_id', '!=', False)], string='Employees')
    assignation_method = fields.Selection([
        ('random', 'Random'),
        ('chosen', 'Chosen by the Customer')], string='Assignation Method', default='random',
        help="How employees will be assigned to meetings customers book on your website.")
    partner_id = fields.Many2one('res.partner', string='Customer')

    @api.model
    def create(self, values):
        res= super(CalendarAppointmentType, self).create(values)
        res.partner_id.sudo().write({'appointment_type':res.id})
        return res

    def _compute_appointment_count(self):
        meeting_data = self.env['calendar.event'].read_group([('appointment_type_id', 'in', self.ids)], ['appointment_type_id'], ['appointment_type_id'])
        mapped_data = {m['appointment_type_id'][0]: m['appointment_type_id_count'] for m in meeting_data}
        for appointment_type in self:
            appointment_type.appointment_count = mapped_data.get(appointment_type.id, 0)

    # def _compute_website_url(self):
    #     for appointment_type in self:
    #         appointment_type.website_url = '/website/calendar/%s/appointment' % (slug(appointment_type))

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = default or {}
        default['name'] = self.name + _(' (copy)')
        return super(CalendarAppointmentType, self).copy(default=default)

    def action_calendar_meetings(self):
        self.ensure_one()
        action = self.env.ref('calendar.action_calendar_event').read()[0]
        action['domain'] = [('appointment_type_id', '=',self.id)]
        action['context'] = {
            'default_appointment_type_id': self.id,

        }
        return action

    # --------------------------------------
    # Slots Generation
    # --------------------------------------

    def _slots_generate(self, first_day, last_day, timezone):
        """ Generate all appointment slots (in naive UTC, appointment timezone, and given (visitors) timezone)
            between first_day and last_day (datetimes in appointment timezone)

            :return: [ {'slot': slot_record, <timezone>: (date_start, date_end), ...},
                      ... ]
        """
        def append_slot(day, slot):
            local_start = appt_tz.localize(datetime.combine(day, time(hour=int(slot.hour), minute=int(round((slot.hour % 1) * 60)))))
            local_end = appt_tz.localize(
                datetime.combine(day, time(hour=int(slot.hour), minute=int(round((slot.hour % 1) * 60)))) + relativedelta(hours=self.appointment_duration))
            slots.append({
                self.appointment_tz: (
                    local_start,
                    local_end,
                ),
                timezone: (
                    local_start.astimezone(requested_tz),
                    local_end.astimezone(requested_tz),
                ),
                'UTC': (
                    local_start.astimezone(pytz.UTC).replace(tzinfo=None),
                    local_end.astimezone(pytz.UTC).replace(tzinfo=None),
                ),
                'slot': slot,
            })
        appt_tz = pytz.timezone(self.appointment_tz)
        requested_tz = pytz.timezone(timezone)

        slots = []
        for slot in self.slot_ids.filtered(lambda x: int(x.weekday) == first_day.isoweekday()):
            if slot.hour > first_day.hour + first_day.minute / 60.0:
                append_slot(first_day.date(), slot)
        slot_weekday = [int(weekday) - 1 for weekday in self.slot_ids.mapped('weekday')]
        for day in rrule.rrule(rrule.DAILY,
                               dtstart=first_day.date() + timedelta(days=1),
                               until=last_day.date(),
                               byweekday=slot_weekday):
            for slot in self.slot_ids.filtered(lambda x: int(x.weekday) == day.isoweekday()):
                append_slot(day, slot)
        return slots

    def _slots_available(self, slots, first_day, last_day, employee=None):
        """ Fills the slot stucture with an available employee

            :param slots: slots structure generated by _slots_generate
            :param first_day: start datetime in UTC
            :param last_day: end datetime in UTC
            :param employee: if set, only consider this employee
                             if not set, consider all employees assigned to this appointment type
        """

        def is_work_available(start_dt, end_dt, intervals):
            """ check if the slot is contained in the employee's work hours (defined by intervals)
            """
            def find_start_index():
                """ find the highest index of intervals for which the start_date (element [0]) is before (or at) start_dt
                """
                def recursive_find_index(lower_bound, upper_bound):
                    if upper_bound - lower_bound <= 1:
                        if intervals[upper_bound][0] <= start_dt:
                            return upper_bound
                        return lower_bound
                    index = (upper_bound + lower_bound) // 2
                    if intervals[index][0] <= start_dt:
                        return recursive_find_index(index, upper_bound)
                    else:
                        return recursive_find_index(lower_bound, index)

                if start_dt <= intervals[0][0] - tolerance:
                    return -1
                if end_dt >= intervals[-1][1] + tolerance:
                    return -1
                return recursive_find_index(0, len(intervals) - 1)

            if not intervals:
                return False

            tolerance = timedelta(minutes=1)
            start_index = find_start_index()
            if start_index != -1:
                for index in range(start_index, len(intervals)):
                    if intervals[index][1] >= end_dt - tolerance:
                        return True
                    if len(intervals) == index + 1 or intervals[index + 1][0] - intervals[index][1] > tolerance:
                        return False
            return False

        def is_calendar_available(slot, events, employee):
            """ Returns True if the given slot doesn't collide with given events for the employee
            """
            start_dt = slot['UTC'][0]
            end_dt = slot['UTC'][1]

            event_in_scope = lambda ev: (
                fields.Date.to_date(ev.start) <= fields.Date.to_date(end_dt)
                and fields.Date.to_date(ev.stop) >= fields.Date.to_date(start_dt)
            )

            for ev in events.filtered(event_in_scope):
                if ev.allday:
                    # allday events are considered to take the whole day in the related employee's timezone
                    event_tz = pytz.timezone(ev.event_tz or employee.user_id.tz or self.env.user.tz or slot['slot'].appointment_type_id.appointment_tz or 'UTC')
                    ev_start_dt = datetime.combine(fields.Date.from_string(ev.start_date), time.min)
                    ev_stop_dt = datetime.combine(fields.Date.from_string(ev.stop_date), time.max)
                    ev_start_dt = event_tz.localize(ev_start_dt).astimezone(pytz.UTC).replace(tzinfo=None)
                    ev_stop_dt = event_tz.localize(ev_stop_dt).astimezone(pytz.UTC).replace(tzinfo=None)
                    if ev_start_dt < end_dt and ev_stop_dt > start_dt:
                        return False
                elif fields.Datetime.to_datetime(ev.start_datetime) < end_dt and fields.Datetime.to_datetime(ev.stop_datetime) > start_dt:
                    return False
            return True

        workhours = {}
        meetings = {}

        # With context will be used in resource.calendar to force the referential user
        # for work interval computing to the *user linked to the employee*
        available_employees = [emp.with_context(tz=emp.user_id.tz) for emp in (employee or self.employee_ids)]
        random.shuffle(available_employees)
        for slot in slots:
            for emp_pos, emp in enumerate(available_employees):
                if emp_pos not in workhours:
                    workhours[emp_pos] = [
                        (interval[0].astimezone(pytz.UTC).replace(tzinfo=None),
                         interval[1].astimezone(pytz.UTC).replace(tzinfo=None))
                        for interval in emp.resource_calendar_id._work_intervals(
                            first_day, last_day, resource=emp.resource_id,
                        )
                    ]

                if is_work_available(slot['UTC'][0], slot['UTC'][1], workhours[emp_pos]):
                    if emp_pos not in meetings:
                        # note: no check is made on the attendee's status (accepted/declined/...)
                        meetings[emp_pos] = self.env['calendar.event'].search([
                            ('partner_ids.user_ids', '=', emp.user_id.id),
                            ('start', '<', fields.Datetime.to_string(last_day.replace(hour=23, minute=59, second=59))),
                            ('stop', '>', fields.Datetime.to_string(first_day.replace(hour=0, minute=0, second=0)))
                        ])

                    if is_calendar_available(slot, meetings[emp_pos], emp):
                        slot['employee_id'] = emp
                        break

    def _get_appointment_slots(self, timezone, employee=None):
        """ Fetch available slots to book an appointment
            :param timezone: timezone string e.g.: 'Europe/Brussels' or 'Etc/GMT+1'
            :param employee: if set will only check available slots for this employee
            :returns: list of dicts (1 per month) containing available slots per day per week.
                      complex structure used to simplify rendering of template
        """
        self.ensure_one()
        appt_tz = pytz.timezone(self.appointment_tz)
        requested_tz = pytz.timezone(timezone)
        first_day = requested_tz.fromutc(datetime.utcnow() + relativedelta(hours=self.min_schedule_hours))
        last_day = requested_tz.fromutc(datetime.utcnow() + relativedelta(days=self.max_schedule_days))

        # Compute available slots (ordered)
        slots = self._slots_generate(first_day.astimezone(appt_tz), last_day.astimezone(appt_tz), timezone)
        # if not employee or employee in self.employee_ids:
        #     self._slots_available(slots, first_day.astimezone(pytz.UTC), last_day.astimezone(pytz.UTC), employee)
        # Compute calendar rendering and inject available slots
        today = requested_tz.fromutc(datetime.utcnow())
        start = today
        month_dates_calendar = cal.Calendar(0).monthdatescalendar
        months = []
        while (start.year, start.month) <= (last_day.year, last_day.month):
            dates = month_dates_calendar(start.year, start.month)
            for week_index, week in enumerate(dates):
                for day_index, day in enumerate(week):
                    mute_cls = weekend_cls = today_cls = None
                    today_slots = []
                    if day.weekday() in (cal.SUNDAY, cal.SATURDAY):
                        weekend_cls = 'o_weekend'
                    if day == today.date() and day.month == today.month:
                        today_cls = 'o_today'
                    if day.month != start.month:
                        mute_cls = 'text-muted o_mute_day'
                    else:
                        # slots are ordered, so check all unprocessed slots from until > day

                        while slots and (slots[0][timezone][0].date() <= day):
                            if self.env.company.is_single_booking == True:
                                cal_event = self.env['calendar.event'].search([('start','=',slots[0][timezone][0])])
                                if not cal_event:
                                    if (slots[0][timezone][0].date() == day):
                                        today_slots.append({
                                            'datetime': slots[0][timezone][0].strftime('%Y-%m-%d %H:%M:%S'),
                                            'hours': slots[0][timezone][0].strftime('%H:%M')
                                        })
                            else:
                                if (slots[0][timezone][0].date() == day):
                                    today_slots.append({
                                        'datetime': slots[0][timezone][0].strftime('%Y-%m-%d %H:%M:%S'),
                                        'hours': slots[0][timezone][0].strftime('%H:%M')
                                    })
                            slots.pop(0)
                    dates[week_index][day_index] = {
                        'day': day,
                        'slots': today_slots,
                        'mute_cls': mute_cls,
                        'weekend_cls': weekend_cls,
                        'today_cls': today_cls
                    }

            months.append({
                'month': format_datetime(start, 'MMMM Y', locale=get_lang(self.env).code),
                'weeks': dates
            })
            start = start + relativedelta(months=1)
        return months


class CalendarAppointmentSlot(models.Model):
    _name = "calendar.appointment.slot"
    _description = "Online Appointment : Time Slot"
    _rec_name = "weekday"
    _order = "weekday, hour"

    appointment_type_id = fields.Many2one('calendar.appointment.type', 'Appointment Type', ondelete='cascade')
    weekday = fields.Selection([
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ('7', 'Sunday'),
    ], string='Week Day', required=True)
    hour = fields.Float('Starting Hour', required=True, default=8.0)
    end_date = fields.Float('Ending Hour',store=True)

    @api.constrains('hour')
    def check_hour(self):
        if any(self.filtered(lambda slot: 0.00 > slot.hour or slot.hour >= 24.00)):
            raise ValidationError(_("Please enter a valid hour between 0:00 to 24:00 for your slots."))

    def name_get(self):
        weekdays = dict(self._fields['weekday'].selection)
        return self.mapped(lambda slot: (slot.id, "%s, %02d:%02d" % (weekdays.get(slot.weekday), int(slot.hour), int(round((slot.hour % 1) * 60)))))

    @api.onchange('hour')
    def check_appoint_hour(self):
        self.end_date = self.hour + self.appointment_type_id.appointment_duration

class CalendarAppointmentQuestion(models.Model):
    _name = "calendar.appointment.question"
    _description = "Online Appointment : Questions"
    _order = "sequence"

    sequence = fields.Integer('Sequence')
    appointment_type_id = fields.Many2one('calendar.appointment.type', 'Appointment Type', ondelete="cascade")
    name = fields.Char('Question', translate=True, required=True)
    placeholder = fields.Char('Placeholder', translate=True)
    question_required = fields.Boolean('Required Answer')
    question_type = fields.Selection([
        ('char', 'Single line text'),
        ('text', 'Multi-line text'),
        ('select', 'Dropdown (one answer)'),
        ('radio', 'Radio (one answer)'),
        ('checkbox', 'Checkboxes (multiple answers)')], 'Question Type', default='char')
    answer_ids = fields.Many2many('calendar.appointment.answer', 'calendar_appointment_question_answer_rel', 'question_id', 'answer_id', string='Available Answers')


class CalendarAppointmentAnswer(models.Model):
    _name = "calendar.appointment.answer"
    _description = "Online Appointment : Answers"

    question_id = fields.Many2many('calendar.appointment.question', 'calendar_appointment_question_answer_rel', 'answer_id', 'question_id', string='Questions')
    name = fields.Char('Answer', translate=True, required=True)

class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    partner_new = fields.Many2one('res.partner', string='attendee')
    start_at = fields.Date()
    start_time = fields.Char(string='Start Time')
    end_time = fields.Char(string='End Time')
    doctore_id = fields.Many2one('res.partner', string='Doctore')


    @api.onchange('doctore_id')
    def onchange_doctore_id(self):
        print("\n\n nside onchange doctore id:,,,:", self)
        print("doctire:", self.id , self.doctore_id, self.doctore_id.name)
        if self.doctore_id:
            print("\n inside doctore if:", self.doctore_id)
            self.sudo().write({'partner_ids': [Command.link(self.doctore_id.id)]})

    def _default_access_token(self):
        return str(uuid.uuid4())

    access_token = fields.Char('Access Token', default=_default_access_token, readonly=True)
    appointment_type_id = fields.Many2one('calendar.appointment.type', 'Online Appointment', readonly=True)

    def _compute_is_highlighted(self):
        super(CalendarEvent, self)._compute_is_highlighted()
        if self.env.context.get('active_model') == 'calendar.appointment.type':
            appointment_type_id = self.env.context.get('active_id')
            for event in self:
                if event.appointment_type_id.id == appointment_type_id:
                    event.is_highlighted = True

    def _init_column(self, column_name):
        """ Initialize the value of the given column for existing rows.
            Overridden here because we skip generating unique access tokens
            for potentially tons of existing event, should they be needed,
            they will be generated on the fly.
        """
        if column_name != 'access_token':
            super(CalendarEvent, self)._init_column(column_name)

    def _generate_access_token(self):
        for event in self:
            event.access_token = self._default_access_token()

    @api.model
    def get_value_price(self):
        cr = self._cr

        query = """
        SELECT cl.start AS date_time,count(*) as count
        FROM calendar_event cl 
        group by cl.start
        order by cl.start

        """
        cr.execute(query)
        partner_data = cr.dictfetchall()
        partner_day = []
        data_set = {}
        mydate = []
        mycount = []
        list_value = []
        dict={} 
        count = 0
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                         "Friday", "Saturday", "Sunday"]
        for data in partner_data:
            if data['date_time']:
                mydate = data['date_time'].weekday()
                if mydate >= 0:
                    value = days[mydate]
                    list_value.append(value)
                    
                    list_value1 = list(set(list_value))

                    for record in list_value1:
                        count = 0
                        for rec in list_value:
                            if rec ==record:
                                count = count+1
                            dict.update({record:count})
                        keys, values = zip(*dict.items())
                        data_set.update({"data":dict})
        return data_set

    @api.model
    def get_monthly_appointments(self):
        cr = self._cr

        query = """
        SELECT cl.start AS date_time,count(*) as count
        FROM calendar_event cl 
        group by cl.start
        order by cl.start

        """
        cr.execute(query)
        partner_data = cr.dictfetchall()
        partner_day = []
        data_set = {}
        mycount = []
        list_value = []
        
        dict={} 
        count = 0

        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                'August', 'September', 'October', 'November', 'December']
    
        for data in partner_data:
            if data['date_time']:
                mydate = data['date_time'].month
                for month_idx in range(0, 13):
                    if mydate == month_idx:
                        value = cal.month_name[month_idx]
                        list_value.append(value)
                        list_value1 = list(set(list_value))
                        for record in list_value1:
                            count = 0
                            for rec in list_value:
                                if rec ==record:
                                    count = count+1
                                dict.update({record:count})
                        keys, values = zip(*dict.items())
                        data_set.update({"data":dict})
        return data_set
