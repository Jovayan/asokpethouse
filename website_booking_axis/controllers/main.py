# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import uuid
from babel.dates import format_datetime, format_date
from datetime import date, datetime
from werkzeug.urls import url_encode

from odoo import http, _, fields, Command
from odoo.http import request
from odoo.tools import html2plaintext, DEFAULT_SERVER_DATETIME_FORMAT as dtf
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools.misc import get_lang
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.exceptions import ValidationError

class WebsiteCalendar(http.Controller): 
    
    @http.route([
        '/appointment/select',
    ], type='http', auth="public", website=True)
    def appointment_country_choice(self, message=None, **kwargs):
        appoint_with_state = request.env['appointment.group'].sudo().search([('state_id', '!=', False)])
        appoint_without_state = request.env['appointment.group'].sudo().search([('state_id', '=', False)])

        appoint_groups_ids = []
        state_list = []
        for rec in appoint_with_state:
            if rec.state_id.id not in state_list:
                appoint_groups_ids.append(rec.id)
                state_list.append(rec.state_id.id)

        country_list = []
        for rec in appoint_without_state:
            if rec.country_id.id not in country_list:
                appoint_groups_ids.append(rec.id)
                country_list.append(rec.country_id.id)

        appoint_group = request.env['appointment.group'].sudo().search([('id', 'in', appoint_groups_ids)])
        value = {'appoint_group': appoint_group}
        return request.render("website_booking_axis.appointment_country", value)

    @http.route([
        '/appointment/',
        '/appointment/<int:state_id>',
    ], type='http', auth="public", website=True)
    def appointment_group_choice(self,state_id=None,  appointment_type=None,
                                 employee_id=None, message=None, **post):
        domain = [('country_id', '=', int(post.get('country_id')))]
        if state_id:
            domain += [('state_id', '=', state_id)]
        appoint_group = request.env['appointment.group'].sudo().search(domain)
        appoint_group_id = request.env['appointment.group'].sudo().search([('id', '=', post.get('group_id'))])
        value={
            'appoint_group':appoint_group,
            'appoint_group_id': appoint_group_id.id,
        }
        return request.render("website_booking_axis.appointment_1", value)

    @http.route(['/website/appointment'], type='http', auth="public", website=True) # issue reason method=["POST"],
    def appointees_info(self, prev_emp=False, **post):
        country_id = post.get('country_id')
        if 'id' in post:
            appoint_group_ids = request.env['appointment.group'].sudo().search([('id','=', post.get('id'))])
        partner_ids = []
        # appointment_type = []
        for record in appoint_group_ids:
            for rec in record.appointment_group_ids:
                partner_ids.append(rec.id)
                # appointment_type.append(j.appointment_type.id)
        value={
            'appoint_group_ids':appoint_group_ids,
            'country':country_id,
            # 'appointment_type': appointment_type
        }
        return request.render("website_booking_axis.appointees_availability",value)

    @http.route(['/website/appointment/slot'], type='http', auth="public", website=True)
    def appointment_slots(self,appointment_type=None,timezone=None, prev_emp=False, **post):
        appoint_group_id = request.env['appointment.group'].sudo().search([('id','=',post.get('product_id'))])
        country_id = post.get('country_id')
        appointment_timeslots = request.env['res.partner'].sudo().search([('id','=', post.get('id'))])
        appointment_type = request.env['calendar.appointment.type'].sudo().search([('partner_id.id','=',post.get('id'))])
        value = {}
        if appointment_type:
            request.session['timezone'] = timezone or appointment_type.appointment_tz
            Slots = appointment_type.sudo()._get_appointment_slots(request.session['timezone'], appointment_type)
            value.update({
                'appointment_type':appointment_type,
                'slots':Slots,
                'country_id':country_id,
                'appoint_group_id': appoint_group_id

            })
            return request.render("website_booking_axis.slot", value)
        else:
            return request.render("website_booking_axis.slot_available")

    @http.route(['/website/appointment/form/<model("calendar.appointment.type"):appointment_type>/info'], type='http', auth="public", website=True)
    def appointment_form(self,appointment_type, **post):
        appoint_group_id = request.env['appointment.group'].sudo().search([('id', '=', post.get('group_product_id'))])

        request.session['partner_get'] = appointment_type.partner_id.id
        country_id = post.get("country")
        partner_id = request.env['res.partner'].sudo().search([('id','=',request.env.user.partner_id.id)])
        partner_data = {}
        if request.env.user.partner_id != request.env.ref('base.public_partner'):
            partner_data = request.env.user.partner_id.read(fields=['name', 'mobile', 'country_id', 'email'])[0]
        date_time = post.get('date_time')
        day_name = format_datetime(datetime.strptime(date_time, dtf), 'EEE', locale=get_lang(request.env).code)
        date_formated = format_datetime(datetime.strptime(date_time, dtf), locale=get_lang(request.env).code)
        country_get = request.env['appointment.group'].sudo().search([])

        return request.render("website_booking_axis.appointment_form", {
            'partner_data': partner_data,
            'appointment_type': appointment_type,
            'datetime': date_time,
            'datetime_locale': day_name + ' ' + date_formated,
            'datetime_str': date_time,
            'country': country_id,
            'partner_name':partner_id.name,
            'partner_email':partner_id.email,
            'partner_phone':partner_id.phone,
            'appoint_group_id': appoint_group_id
        })

    # @http.route('/website/calendar/<model("calendar.appointment.type"):appointment_type>/undefined', type='json', auth="public", website=True, method=["POST"])
    # def appointment_payment_transaction(self,  access_token, **kwargs):
    #     print("nappointment_payment_transaction:", kwargs)
    #     print("appointment_payment_transaction:", self, '=>', access_token)
    #     """ Create a draft transaction and return its processing values.
    #
    #     :param int order_id: The sales order to pay, as a `sale.order` id
    #     :param str access_token: The access token used to authenticate the request
    #     :param dict kwargs: Locally unused data passed to `_create_transaction`
    #     :return: The mandatory values for the processing of the transaction
    #     :rtype: dict
    #     :raise: ValidationError if the invoice id or the access token is invalid
    #     """
    #     # Check the order id and the access token
    #     try:
    #         # self._document_check_access('sale.order', order_id, access_token)
    #         pass
    #     except MissingError as error:
    #         raise error
    #     except AccessError:
    #         raise ValidationError("The access token is invalid.")
    #
    #     kwargs.update({
    #         'reference_prefix': None,  # Allow the reference to be computed based on the order
    #         # 'sale_order_id': order_id,  # Include the SO to allow Subscriptions to tokenize the tx
    #     })
    #     kwargs.pop('custom_create_values', None)  # Don't allow passing arbitrary create values
    #     tx_sudo = self._create_transaction(
    #         custom_create_values={'sale_order_ids': [Command.set([kwargs('payment_option_id')])]}, **kwargs,
    #     )
    #
    #     # Store the new transaction into the transaction list and if there's an old one, we remove
    #     # it until the day the ecommerce supports multiple orders at the same time.
    #     last_tx_id = request.session.get('__website_sale_last_tx_id')
    #     last_tx = request.env['payment.transaction'].browse(last_tx_id).sudo().exists()
    #     if last_tx:
    #         PaymentPostProcessing.remove_transactions(last_tx)
    #     request.session['__website_sale_last_tx_id'] = tx_sudo.id
    #
    #     return tx_sudo._get_processing_values()

    @http.route(['/website/calendar/<model("calendar.appointment.type"):appointment_type>/submit'], type='http',
                auth="public", website=True, method=["POST"])
    def calendar_appointment_submit(self, appointment_type, country_id=False, **kwargs):
        appoint_group_id = request.env['appointment.group'].sudo().search([('id', '=', kwargs.get('appoint_group_id'))])
        name = kwargs.get('name') or ''
        phone = kwargs.get('phone') or ''
        last_name = kwargs.get('last_name') or ''
        description = kwargs.get('description') or ''
        email = kwargs.get('email') or ''
        datetime_str = kwargs.get('date_time')
        date_start = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        date_end = date_start + relativedelta(hours=appointment_type.appointment_duration)

        if request.env.company.is_single_booking == True:
            cal_event = request.env['calendar.event'].sudo().search([('start', '=', date_start)])
            # print("cal_event::::::::::::::::::::::",cal_event)
            if cal_event:
                raise ValidationError("This Slot is Already Booked Kindly select another one!")

        country_id = int(country_id) if country_id else None
        country_name = country_id and request.env['res.country'].browse(country_id).name or ''
        #Partner = request.env['res.partner'].sudo().search([('id','=', partner)])
        Partner = request.env['res.partner'].sudo().search([('email', '=like', email)], limit=1)

        if Partner:
            if not Partner.mobile or len(Partner.mobile) <= 5 and len(phone) > 5:
                Partner.write({'mobile': phone,
                               'last_name': last_name,
                               'comment': description})
            if not Partner.country_id:
                Partner.country_id = country_id
            Partner.start_datetime = date_start.strftime(dtf)
        else:
            Partner = request.env['res.partner'].sudo().create({
                'name': name,
                'country_id': country_id,
                'mobile': phone,
                'email': email,
                'start_datetime': date_start.strftime(dtf),
                'last_name': last_name,
                'comment': description
            })
        attendee = Partner.name
        description = ('Attendee: %s\n'
                       'Country: %s\n'
                       'Mobile: %s\n'
                       'Email: %s\n'
                       'Note: %s\n' % (attendee, country_name, phone, email, description))

        for question in appointment_type.question_ids:
            key = 'question_' + str(question.id)
            if question.question_type == 'checkbox':
                answers = question.answer_ids.filtered(lambda x: (key + '_answer_' + str(x.id)) in kwargs)
                description += question.name + ': ' + ', '.join(answers.mapped('name')) + '\n'
            elif kwargs.get(key):
                if question.question_type == 'text':
                    description += '\n* ' + question.name + ' *\n' + kwargs.get(key, False) + '\n\n'
                else:
                    description += question.name + ': ' + kwargs.get(key) + '\n'

        #categ_id = request.env.ref('website_booking_axis.calendar_event_type_data_online_appointment')
        #alarm_ids = appointment_type.reminder_ids and [(6, 0, appointment_type.reminder_ids.ids)] or []
        start_time = str(date_start.time())
        end_time = str(date_end.time())

        event = request.env['calendar.event'].sudo().create({
            'name': appointment_type.name,
            'start': date_start.strftime(dtf),
            'start_at':date_start.date(),
            'stop': date_end,
            'description': description,
            'partner_new': Partner.id,
            #'partner_ids': [Command.link(Partner.id)],
            'appointment_type_id': appointment_type.id,
            'start_time':start_time,
            'end_time':end_time,
            #'doctore_id' : appointment_type.partner_id.id


        })
        calendar_attendee = request.env['calendar.attendee'].sudo().create(
            {'partner_id': Partner.id,
             'state': 'needsAction',
             'email': email,
             'event_id': event.id})

        event.write({'attendee_ids': [(6, 0, [i.id for i in calendar_attendee])]})
        request.session['event'] = event.id
        product_list = []
        product_dict = {}
        partner_get = request.session.get('partner_get')
        partner = request.env['res.partner'].sudo().search([('id','=', partner_get)])

        product = request.env['product.product'].sudo().search([('name','ilike',appoint_group_id.product_template_id.name)])
        order = request.env['sale.order'].sudo().create({
            'partner_id': Partner.id,
            'partner_shipping_id': appointment_type.partner_id.id,
            'order_line':[(0, 0, {
                    'product_id':product.id,
                    'price_unit':partner.appointment_charge,
                })],
        })
        acquirers = request.env['payment.provider'].sudo().search([('state','!=','disabled')])
        order_data = request.website.sale_get_order()
        if order:
            request.session['sale_order_id'] = order.id
        request.session['sale_last_order_id'] = order.id
        value = {
            'event': event,
            'start_time':start_time,
            'end_time':end_time,
            #'website_sale_order':order,
            #'acquirers':acquirers,
            #'order_id':order.id,
            #'access_token': str(uuid.uuid4()),
            #'success_url': 'shop/payment/transaction',
            #'error_url':'error',
            #'callback_method':'callback_method',
            #'order': order,
        }
        print("\n-Last PArt---- Payment opton:", value)
        # return request.render('website_booking_axis.payment_option',value)
        # return request.redirect('/shop/confirmation')
        # return request.redirect('/appointment/confirmation')
        print("user|:| partner...:", request.env.user, request.env.user.name, ":", request.env.user.partner_id,  request.env.user.partner_id.name)
        # if not request.env.user:
        #     print("\n inside if usser")
        #     return request.redirect('/shop/cart')
        # else:
        #     print("\n inside nottt -if usser")
        #
        #     return request.redirect('/shop/cart')
        return request.render('website_booking_axis.appointment_confirm', value)

    @http.route('/appointment/confirmation', type='http', auth="public", website=True, sitemap=False)
    def payment_validate(self, **kwargs):
        sale_order_id = request.session.get('sale_last_order_id')
        order = request.env['sale.order'].sudo().search([('id','=', sale_order_id)])
        event_id = request.session.get('event')
        event = request.env['calendar.event'].sudo().browse(event_id)
        value = {
            'event':event,
            'order':order,
        }
        return request.render('website_booking_axis.appointment_confirm',value)

    #-----------start-----
    #
    # def checkout_redirection(self, order):
    #     # must have a draft sales order with lines at this point, otherwise reset
    #     if not order or order.state != 'draft':
    #         request.session['sale_order_id'] = None
    #         request.session['sale_transaction_id'] = None
    #         return request.redirect('/shop')
    #
    #     if order and not order.order_line:
    #         return request.redirect('/shop/cart')
    #
    #     # if transaction pending / done: redirect to confirmation
    #     tx = request.env.context.get('website_sale_transaction')
    #     if tx and tx.state != 'draft':
    #         return request.redirect('/shop/payment/confirmation/%s' % order.id)
    #
    # @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    # def address(self, **kw):
    #     print("\n\n shop adrreesss:,,,,,:", kw)
    #     Partner = request.env['res.partner'].with_context(show_address=1).sudo()
    #     order = request.website.sale_get_order()
    #     print("ordro:", order)
    #     redirection = self.checkout_redirection(order)
    #     if redirection:
    #         return redirection
    #
    #     mode = (False, False)
    #     can_edit_vat = False
    #     values, errors = {}, {}
    #
    #     partner_id = int(kw.get('partner_id', -1))
    #     print("partner id:", partner_id)
    #
    #     # IF PUBLIC ORDER
    #     if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
    #         print("if :partner id:", partner_id)
    #         mode = ('new', 'billing')
    #         can_edit_vat = True
    #     # IF ORDER LINKED TO A PARTNER
    #     else:
    #         print("else :partner id:", partner_id)
    #         if partner_id > 0:
    #             if partner_id == order.partner_id.id:
    #                 mode = ('edit', 'billing')
    #                 can_edit_vat = order.partner_id.can_edit_vat()
    #             else:
    #                 shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
    #                 if order.partner_id.commercial_partner_id.id == partner_id:
    #                     mode = ('new', 'shipping')
    #                     partner_id = -1
    #                 elif partner_id in shippings.mapped('id'):
    #                     mode = ('edit', 'shipping')
    #                 else:
    #                     # return Forbidden()
    #                     pass
    #             if mode and partner_id != -1:
    #                 values = Partner.browse(partner_id)
    #         elif partner_id == -1:
    #             mode = ('new', 'shipping')
    #         else:  # no mode - refresh without post?
    #             print("nested else:", partner_id)
    #             return request.redirect('/shop/checkout')
    #
    #     # IF POSTED
    #     if 'submitted' in kw:
    #         print("\n if submiteted")
    #         pre_values = self.values_preprocess(order, mode, kw)
    #         errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
    #         post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)
    #
    #         if errors:
    #             errors['error_message'] = error_msg
    #             values = kw
    #         else:
    #             print("if submiteted--- else")
    #             partner_id = self._checkout_form_save(mode, post, kw)
    #             if mode[1] == 'billing':
    #                 order.partner_id = partner_id
    #                 order.with_context(not_self_saleperson=True).onchange_partner_id()
    #                 # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
    #                 order.partner_invoice_id = partner_id
    #                 if not kw.get('use_same'):
    #                     kw['callback'] = kw.get('callback') or \
    #                                      (not order.only_services and (
    #                                                  mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
    #             elif mode[1] == 'shipping':
    #                 order.partner_shipping_id = partner_id
    #
    #             # TDE FIXME: don't ever do this
    #             # -> TDE: you are the guy that did what we should never do in commit e6f038a
    #             order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
    #             if not errors:
    #                 return request.redirect(kw.get('callback') or '/shop/confirm_order')
    #     mode = ('new', 'shipping')
    #     print("\n before render value", mode)
    #     render_values = {
    #         'website_sale_order': order,
    #         'partner_id': partner_id,
    #         'mode': mode,
    #         'checkout': values,
    #         'can_edit_vat': can_edit_vat,
    #         'error': errors,
    #         'callback': kw.get('callback'),
    #         'only_services': order and order.only_services,
    #     }
    #
    #     render_values.update(self._get_country_related_render_values(kw, render_values))
    #     print("\---adrres final:..:", render_values)
    #     return request.render("website_sale.address", render_values)
    #
    # def _get_country_related_render_values(self, kw, render_values):
    #     '''
    #     This method provides fields related to the country to render the website sale form
    #     '''
    #     values = render_values['checkout']
    #     mode = render_values['mode']
    #     order = render_values['website_sale_order']
    #
    #     def_country_id = order.partner_id.country_id
    #     # IF PUBLIC ORDER
    #     if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
    #         country_code = request.session['geoip'].get('country_code')
    #         if country_code:
    #             def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
    #         else:
    #             def_country_id = request.website.user_id.sudo().country_id
    #
    #     country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
    #     country = country and country.exists() or def_country_id
    #
    #     res = {
    #         'country': country,
    #         'country_states': country.get_website_sale_states(mode=mode[1]),
    #         'countries': country.get_website_sale_countries(mode=mode[1]),
    #     }
    #     return res
    #
    # def values_preprocess(self, order, mode, values):
    #     # Convert the values for many2one fields to integer since they are used as IDs
    #     partner_fields = request.env['res.partner']._fields
    #     return {
    #         k: (bool(v) and int(v)) if k in partner_fields and partner_fields[k].type == 'many2one' else v
    #         for k, v in values.items()
    #     }

    #-------end-----


class WebsiteSale(WebsiteSale):

    # @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    # def payment_confirmation(self, **post):
    #     """ End of checkout process controller. Confirmation is basically seing
    #     the status of a sale.order. State at this point :
    #
    #      - should not have any context / session info: clean them
    #      - take a sale.order id, because we request a sale.order and are not
    #        session dependant anymore
    #     """
    #     sale_order_id = request.session.get('sale_last_order_id')
    #     event_id = request.session.get('event')
    #     if (sale_order_id and event_id):
    #         order = request.env['sale.order'].sudo().browse(sale_order_id)
    #         return request.redirect('/appointment/confirmation')
    #     else:
    #         if (sale_order_id and not event_id):
    #             order = request.env['sale.order'].sudo().browse(sale_order_id)
    #             return request.render("website_sale.confirmation", {'order': order})
    #         else:
    #             return request.redirect('/shop')

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :

         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
        sale_order_id = request.session.get('sale_last_order_id')
        event_id = request.session.get('event')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            return request.redirect('/appointment/confirmation')
        else:
            if (sale_order_id and not event_id):
                order = request.env['sale.order'].sudo().browse(sale_order_id)
                return request.render("website_sale.confirmation", {'order': order})
            else:
                return request.redirect('/shop')


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        user = request.env.user
        is_admin = request.env['res.users'].browse(user.id)._is_admin()
        if is_admin:
            calender_list = request.env['calendar.event'].search([])
            calender_ids= [i.id for i in calender_list if i.doctore_id]
            values['appointment_count'] = request.env['calendar.event'].search_count([('id', 'in', calender_ids)])
        else:
            values['appointment_count'] = request.env['calendar.event'].sudo().search_count([('doctore_id','=',user.partner_id.id)])        
        if values.get('sales_user', False):
            values['title'] = _("Salesperson")
        return values

    def _ticket_get_page_view_values(self, appointments, access_token, **kwargs):
        values = {
            'page_name': 'appointments',
            'appointments': appointments,
        }
        return self._get_page_view_values(appointments, access_token, values, False, **kwargs)

    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def my_appointments(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = []
        is_admin = request.env['res.users'].browse(user.id)._is_admin()

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'id': {'input': 'id', 'label': _('Search ID')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('id', 'all'):
                search_domain = OR([search_domain, [('id', 'ilike', search)]])
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            domain += search_domain
        if is_admin:
            calender_list = request.env['calendar.event'].search([])
            calender_ids= [i.id for i in calender_list if i.doctore_id]
            domain += [('id', 'in', calender_ids)]
            appointments = request.env['calendar.event'].search(domain)
        else:
            appointments = request.env['calendar.event'].sudo().search([('doctore_id','=',user.partner_id.id)])
        values.update({
            'appointments': appointments,
            })

        return request.render("website_booking_axis.portal_appointment_layout",values)

    @http.route([
        '/my/appointment/<int:appointment_id>'
    ], type='http', auth="user", website=True)
    def appointments_followup(self, appointment_id=None, **kw):
        appointment = request.env['calendar.event'].sudo().search([('id', '=', int(appointment_id))])
        values = self._prepare_portal_layout_values()
        date_end = appointment.start + relativedelta(hours=appointment.duration)
        start_time = appointment.start.time()
        end_time = date_end.time()
        appointment_description = request.env['res.partner'].search([('name','=',appointment.name)])
        values.update({
            'appointment': appointment,
            'start_time': start_time,
            'end_time': end_time,
            'appointment_description':appointment_description.appointment_group_ids.product_template_id.description
            })
        return request.render("website_booking_axis.appointments_followup",values)        
