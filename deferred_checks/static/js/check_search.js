odoo.define('deferred_checks.check_search', function (require) {
    "use strict";
    
    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    
    var QWeb = core.qweb;
    var _t = core._t;
    
    var CheckSearch = Widget.extend({
        events: {
            "keypress .o_form_input": function(e){
                if(e.keyCode == 13){ //enter 
                    $('.search_btn').click();
                }
            }
        }
    });
    
    core.action_registry.add('check_search_okay', CheckSearch);
    
    return CheckSearch;
    
    });