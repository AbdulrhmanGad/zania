odoo.define('ringdesk.menu_switcher', function (require) {
"use strict";
var Widget = require('web.Widget');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');

var RingdeskWidget = Widget.extend({
    name: 'ringdesk_menu',
    template: 'ringdesk.options_menu',
    start: function() {
        this.$el.append(
            "<button class='ringdesk_btn' name='id' style='display:none'/>" 
            );
    },
    events: {
        'click button.ringdesk_btn': 'open_pop_up'
    },
    init: function(parent) {
        this._super(parent);
    },
    open_pop_up: function(e) {
       let dataset = e.target.dataset;
      if(dataset && dataset.model && dataset.id) {
        this.do_action({
            'name': 'crm.lead.form',
            'type': 'ir.actions.act_window',
            'views': [[false,"form"]],
            'res_id': parseInt(dataset.id),
            'res_model': `${dataset.model}`,
            'target': 'new',
        })
      }
    }
});

if(window.location.href.indexOf("model=sign.template") <= -1){
    SystrayMenu.Items.push(RingdeskWidget);
    
}
return RingdeskWidget;
});
