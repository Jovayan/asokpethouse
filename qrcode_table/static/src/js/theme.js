odoo.define('qrcode_table_theme.theme', function(require) {
    "use strict";

    var publicWidget = require('web.public.widget');

    publicWidget.registry.ThemeHeaderMain = publicWidget.Widget.extend({
        selector: '.theme_header_main_cl',
        events: {
            'click .open_search_cl': 'OpenSearch',
            'click form .icon-bg': 'SearchCloseItem'
        },
        init: function() {
            this._super.apply(this, arguments);
        },
        start: function() {
            return this._super.apply(this, arguments);
        },
        OpenSearch: function(ev) {
            $(ev.currentTarget).addClass('d-none');
            $(ev.currentTarget).next().removeClass('d-none');
        },
        SearchCloseItem: function(ev) {
            $(ev.currentTarget).closest('form').submit();
        },
    });

});