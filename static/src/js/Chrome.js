odoo.define('qrcode_table.Chrome', function(require) {
    'use strict';

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');
    const PosTableChrome = (Chrome) =>
        class extends Chrome {
            /**
             * @override
             */
            async start() {
                await super.start();
                this.env.services.bus_service.addChannel('table.order');
                this.env.services.bus_service.addEventListener('notification', this._onNotification.bind(this));
            }
            _onNotification({ detail: notifications }) {
                for (var notif of notifications) {
                    if (notif.type == 'table.order' && notif.payload['table_order_display'] != undefined) {
                        var user_id = notif.payload;
                        var n = new Noty({
                            theme: 'light',
                            text: notif.payload.table_order_display.table_order_message,
                            timeout: false,
                            layout: 'topRight',
                            type: 'success',
                            closeWith: ['button'],
                            sounds: {
                                sources: ['/qrcode_table/static/lib/noty/lib/done-for-you.mp3'],
                                volume: 1,
                                conditions: ['docVisible']
                            },
                        });
                        n.show();
                    }
                }
            }
        };
    Registries.Component.extend(Chrome, PosTableChrome);
});