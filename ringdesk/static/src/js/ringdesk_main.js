var odooHelper;
var click2dail;
var localPrefix = 'ringdesk';
odoo.define('ringdesk.service', function (require) {
    "use strict";
    var rpc = require('web.rpc');
    odooHelper = {
        is_leads_activated: async ()=> {
            let leads_right  = await odooHelper.call_python_function('utm.campaign','get_leads_activated')
            if(typeof(leads_right) == 'boolean') {
                return leads_right;
            }
            return false;
        },
        is_oauth_activated: async ()=> {
            let oauth  = await odooHelper.call_python_function('res.config.settings','is_oauth_enabled')
            if(oauth == 'True') {
                return true;
            }
            return false;
        },
        list_model: (model_name,field_list) => {
            return rpc.query({
                model: `${model_name}`,
                method: 'search_read',
                args : [[], field_list],
                context: {}
            })
        },
        searchContactOrleads: (model_name,phoneNumber, field_list) => {
            if(!field_list) {
                field_list = ['name', 'phone', 'mobile']
            }
            phoneNumber = phoneNumber.toString()
            let operator = phoneNumber && phoneNumber.length > 4 ? "like" : "=";
            let searchText =  phoneNumber.substring(phoneNumber.length -7, phoneNumber.length);
            return rpc.query({
                model: model_name,
                method: 'search_read',
                args : [["|",["phone" ,operator,searchText],["mobile" ,operator, searchText]], field_list],
            })
        },
        call_python_function: (model_name,function_name, args =[]) => {
            return rpc.query({
                model: `${model_name}`,
                method: `${function_name}`,
                args : args,
            })
        },
        insert: (model_name,data) => { 
            return rpc.query({
                model: `${model_name}`,
                method: 'create',
                args : [data],
            })
        },
        get_action_id: async (action_name, model) =>{
            let responses = await rpc.query({
                model: 'ir.actions.act_window',
                method: 'search_read',
                args : [["&",["res_model","=", model],["name","=", action_name]]],
            })
            if(responses && Array.isArray(responses)  && responses.length>0 && ('id' in responses[0])) return responses[0].id
            return false
        },
        get_menu_id : async (menu_name, parent_id=false) => {
            // ir_ui_menu
             let responses = await rpc.query({
                model: 'ir.ui.menu',
                method: 'search_read',
                args : [["&",["name","=",menu_name],["parent_id","=", parent_id]]],
            })
           if(responses && Array.isArray(responses) && responses.length>0 && ('id' in responses[0])) return responses[0].id;
           return false
        },
        oauth_login: (app_ringdesk) => {
            return rpc.query({
                model: 'res.config.settings',
                method: 'get_auth_setting',
                args : [],
            }).then(result => {
                Object.assign(result, {ringdesk_popup_redirect_uri : new URL('ringdesk/login', location.origin).href, ringdesk_popup_post_logout_redirect_uri: new URL('ringdesk/logout', location.origin).href} )
                app_ringdesk.setAppConfig(result)
            }).catch(err => {
                console.log(err)
            })
        },
        
        route_to:  ({id,name,model, view_type}) => {
            Promise.all([odooHelper.get_action_id(name,model), odooHelper.get_menu_id(name)]).then(response =>{
                var action_id = response[0], menu_id = response[1];
                if(action_id && menu_id) {
                    window.location.href = `${window.location.origin}/web#id=${id}&action=${action_id}&model=${model}&view_type=${view_type}&menu_id=${menu_id}`
                } else if(action_id) {
                    window.location.href = `${window.location.origin}/web#id=${id}&action=${action_id}&model=${model}&view_type=${view_type}`
                }
            })
        },
        open_view_dialog: (model_name, id)=>{
            let btn = document.querySelector('.ringdesk_btn');
            btn.setAttribute('data-model', model_name);
            btn.setAttribute('data-id', id)
            btn.click()
        },
        click2dial:(window)=>{
            window.onhashchange = function(e) {
                clearTimeout(click2dail);    
                click2dail = setTimeout(()=>{
                    let b = document.querySelectorAll('a[name=phone],a[name=mobile]');
                    if(b){
                        b.forEach((a)=>{
                            a["href"] = "#"
                            a.addEventListener('click',(e)=>{
                                e.preventDefault();
                                let phonenumber = e.target['text'];
                                if(phonenumber) {
                                    phonenumber = phonenumber.toString().split('(').join('').split(')').join('').split('-').join('').split(' ').join('');
                                    try {
                                        app_ringdesk.doCallasIs(phonenumber.toString());
                                    } catch (error) {
                                        console.log("Couldn't call because of ", error)
                                    }
                                }
                                return false;
                            }) 
                        })
                    }
                },1000)
            }
            clearTimeout(click2dail);    
            click2dail = setTimeout(()=>{
                let b = document.querySelectorAll('a[name=phone],a[name=mobile]');
                if(b){
                    b.forEach((a)=>{
                        a["href"] = "#"
                        a.addEventListener('click',(e)=>{
                            e.preventDefault();
                            console.log("Working")
                            let phonenumber = e.target['text'];
                            if(phonenumber) {
                                phonenumber = phonenumber.toString().split('(').join('').split(')').join('').split('-').join('').split(' ').join('');
                                try {
                                    app_ringdesk.doCallasIs(phonenumber.toString());
                                } catch (error) {
                                    console.log("Couldn't call because of ", error)
                                }
                            }
                            return false;
                        })
                    })
                }
            },1000)
        },
        save_open_calldetails: (state) => {
            let parent = general.read_storage(state.index, "odoo_name")
            let user = general.read_ringdesk_storage('user')
            if(parent) {
                const startTime = new Date(state.startTime)
                const connectedTime = new Date(state.connectedTime)
                const endTime = new Date(state.endTime)
                const calldetails = {
                    parent_type: parent.type,
                    parent_id: parent.id,
                    call_id: state.callId,
                    from_name: `${parent.isIncoming ? state.peer_name? state.peer_name:state.peer_number : user.displayName ? user.displayName : user.internalExtension}`,
                    to_name: `${parent.isIncoming ? user.displayName ? user.displayName : user.internalExtension : state.peer_name? state.peer_name:state.peer_number}`,
                    phone: `${state.peer_number}`,
                    phone_status: `${parent.isIncoming? 'INBOUND': 'OUTBOUND'}`,
                    call_start_time: general.convert_date(startTime),
                    call_duration: `${general.get_duration(startTime,connectedTime,endTime)}`,
                    peer_name: state.peer_name,
                    call_end_time : general.convert_date(endTime),
                }
                odooHelper.insert('ringdesk.calldetails', calldetails).then(result => {
                    odooHelper.open_view_dialog('ringdesk.calldetails', result)
                    general.write_storage(state.index, null, "odoo_name")
                }).catch(err=>{
                    console.log("Error::", {err, calldetails})
                })
            }
        }
    }
});

let general = {
    override_peername : (line, name) => {
        let lines = general.read_ringdesk_storage('lines');
        if(lines) {
            if(name!=null || name !="") {
                lines[line].peer_name = name;
                general.write_ringdesk_storage('lines', lines)
                let parentHolder = document.querySelector(`div.phone-lines[index="${parseInt(line)}"] .call-state`)
                if(!parentHolder) return;
                let phoneNumberHolder =  parentHolder.nextSibling;
                phoneNumberHolder.innerHTML = `<div class="f-15" style="position: relative;"> <span class="ringdesk-peer-number">${lines[line].peer_number}</span> <span class="ringdesk-peer-name">${name}</span></div>`
            } 
        }
    },
    write_storage: (line, value, name) => {
        name =  `${localPrefix && localPrefix.length>0 ? localPrefix.toString().concat('.',name) :name}`
        let store = localStorage.getItem(`${name}`);
        if(store) {
            store = JSON.parse(store);
            Object.assign(store, { [line]: value});
            localStorage.setItem(`${name}`, JSON.stringify(store));
        } else {
            localStorage.setItem(`${name}`, JSON.stringify({ [line]: value}));
        }
    },
    read_storage : (line, name) => {
        name =  `${localPrefix && localPrefix.length>0 ? localPrefix.toString().concat('.',name) :name}`
        let store = localStorage.getItem(`${name}`);
        if(store) {
            store = JSON.parse(store);
            if(Object.keys(store).some(x=>x == line)){
                return store[line]
            }
        } 
        return false;
    },
    read_ringdesk_storage:(key) => {
        key =  `${localPrefix && localPrefix.length>0 ? localPrefix.toString().concat('.',key) : key}`
        let store = localStorage.getItem(`${key}`)
        if(store) {
            store = JSON.parse(store)
            return store
        }
        return false;
    },
    write_ringdesk_storage: (key, value) => {
        key =  `${localPrefix && localPrefix.length>0 ? localPrefix.toString().concat('.',key) : key}`
        localStorage.setItem(key,JSON.stringify(value));
    },
    convert_date: (date) => {
       let startTime = new Date(date)
       if(!startTime) startTime = new Date()
       function appendZero(val) {
           if(val<10) return '0' + val.toString();
           return val;
       }
       return  `${startTime.getFullYear()}-${appendZero(startTime.getMonth()+1)}-${appendZero(startTime.getDate())} ${appendZero(startTime.getHours())}:${appendZero(startTime.getMinutes())}:${appendZero(startTime.getSeconds())}`
    },
    get_duration:(startDateTime, connectedDateTime, endDateTime)=> {
        let StartDateTime= startDateTime? new Date(startDateTime): new Date();
        let ConnectedDateTime = connectedDateTime? new Date(connectedDateTime) : null;
        let EndDateTime = endDateTime? new Date(endDateTime) : new Date();
        let currentDate = new Date()
        if(EndDateTime && EndDateTime.getFullYear()<currentDate.getFullYear()) {
            EndDateTime = new Date();
        } 
        if(StartDateTime && StartDateTime.getFullYear()<currentDate.getFullYear()) {
            StartDateTime = null;
        } 
        if(ConnectedDateTime && ConnectedDateTime.getFullYear()<currentDate.getFullYear()) {
            ConnectedDateTime = null;
        } 
        let returnTime;
        if(ConnectedDateTime && EndDateTime) {
            returnTime =  Math.abs(EndDateTime.getTime() - ConnectedDateTime.getTime());
        } if(StartDateTime && EndDateTime) {
            returnTime =  Math.abs(EndDateTime.getTime() - StartDateTime.getTime());
        } else {
            return "0:10 Min"
        }
        var minutes = Math.floor(returnTime / 60000);
        var seconds = ((returnTime % 60000) / 1000).toFixed(0);
        return minutes.toString() + ":" + (seconds < 10 ? '0' : '') + seconds.toString() + " Min";
    },
    add_tab_records: async ({origin,tags,phone_number,model_name, btntext}) => {
        if(!origin) origin = []
        const field_list = tags == 'leads' ? ['name', 'phone', 'mobile', 'company_id'] : ['name', 'phone', 'mobile','parent_id', 'company_name']
        let  records =  await odooHelper.searchContactOrleads(model_name,phone_number, field_list);
        console.log(records)
        if(tags == 'leads') {
            records = await records.map(x=> x.company_id  ? Object.assign(x, {company_name: x.company_id[1] == "YourCompany"? "": x.company_id[1] }) : x)
        } else {
            records = await records.map(x=> {x.company_name = x.parent_id ? x.company_name ? x.company_name : x.parent_id[x.parent_id.length-1] : x.company_name; return x})
        }
        const configs = { id: 'company_name', return: 'id', show: ['name'], headers:['Full Name', 'Company'], databtn: false}
       origin.push({tag: tags, data: records, rules: configs, showbtn: true, btntext : btntext})
       return origin;
    }

}

let checkVendor  = function() {
	let defaultVendor = "";
	exceptionVendorList = ['3CXCloud','Xelion'];
	this.vendorList = async function () {
		pbxConnectors = general.read_ringdesk_storage('pbxConnectors');
		if(pbxConnectors){
			vendor = await Array.from(pbxConnectors.items,x=>{ if(x.isDefault) defaultVendor = x.vendor; return x.vendor;});
			return vendor
		}
		return [];
	};
	this.vendorList();
	Object.defineProperty(this,'defaultVendor',{
		get: function() {
			return defaultVendor;
		}
	})
	Object.defineProperty(this,'extraDialIncomingEvent',{
		get: function() {
			if(defaultVendor && exceptionVendorList.some(x => x === defaultVendor)) return true; 
			 return false;
		}
	})
	Object.defineProperty(this,'exceptionVendorList',{
		get: function() {
			return exceptionVendorList;
		},
		set: function({value, append = true}) {
			if(append) {
				if(!Array.isArray(value)) throw new Error('Invalid input:: Excepting {value::array[strings],append::boolean}')
				exceptionVendorList = Array.from(new Set([...exceptionVendorList, ...value]))
			} else {
				if(!Array.isArray(value)) throw new Error('Invalid input:: Excepting {value::array[strings],append::boolean}')
				exceptionVendorList = Array.from(new Set([...value]))
			}
			
		}
	})
}
