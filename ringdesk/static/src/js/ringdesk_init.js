/*********************
 Ringdesk Config
*******************/
let app_ringdesk;
let is_leads_activated = false;
let is_oauth_activated = false;
(async function  () {
  is_leads_activated = await odooHelper.is_leads_activated()
   is_oauth_activated = await odooHelper.is_oauth_activated()
let ringdeskdefaultConfig = {
    container: "ringdesk-container",
    height: 410,
    width: 400,
    initialState: 'open',
    position: 'bottom-right',
    appName: 'PBX Integration for ODOO',
    titleBarStyle: {
        backgroundColor: '#7c7bad',
        color: '#fff',
        hideMinimizeIcon: false,
        minimizeIcon: 'i-minus',
        minimizeIconStyle: {
            'color': '#fff'
        }
    },
    logo: './img/logo.png',
    filter: {
        'Deny': ['heV', 'proshore']
    },
    contactList: true,
    outboundNormalization: true,
    useloginWithOauth2: is_oauth_activated,
    showTitleBar: true,
    customTabs: is_leads_activated?[{ title : 'Contacts', tag : 'contacts'}, {title: 'Leads', tag: 'leads'}] : [{ title : 'Contacts', tag : 'contacts'}],
    storagePrefix : localPrefix
};
/*********************
Initialize Ringdesk
*******************/
let VenderDetails = new checkVendor();
app_ringdesk = ringdeskApp.init({
    config: ringdeskdefaultConfig,
    events: {
        inbounds: {
            onDial: async (err, phonedata) => {
                if (err) return;
                if (VenderDetails.extraDialIncomingEvent && phonedata.lineData.state == 0) {
                    return; 
                }
               
                general.write_storage(phonedata.line, null , "odoo_name")
                general.write_storage(phonedata.line, false, "call_accepted_line")   
                console.log("Dialing Call", phonedata)
                odooHelper.searchContactOrleads('res.partner',phonedata.phoneNumber).then((data) => {
                    if(Array.isArray(data) && data.length>0) {
                        general.override_peername(phonedata.line, data[0].name);
                        general.write_storage(phonedata.line, {id: data[0].id , name: data[0].name, type: "Contact", isIncoming: false} , "odoo_name")
                    } 
                })
            },
            onHookOff(data) {},
            onOutgoingCallAlerting: (data) => {},
            onCallAccepted:  async (data) => {
                console.log("Accepted Data", data)
               let response = general.read_storage(data.lineData.index, "odoo_name")
               general.write_storage(data.lineData.index, true, "call_accepted_line")
               if(response) {
                   if(response.id == "") return;
                    general.override_peername(data.lineData.index, response.name);
                    let model_name = response.type =='Contact' ? 'res.partner' : 'crm.lead'
                    odooHelper.open_view_dialog(model_name, response.id)
                    
                } else {
                    general.write_storage(data.lineData.index, {id: "" , name: "", type: "", isIncoming: false} , "odoo_name")
                }
                
            },
            onCallEnded: async (data) => {
                let response = general.read_storage(data.lineData.index, "call_accepted_line")
                if(response) {
                    general.write_storage(data.lineData.index, false, "call_accepted_line")
                    odooHelper.save_open_calldetails(data.lineData)
                }
            },
            onCallMute: (data) => {},
            onCallToggle: (data) => {},
            onCallTransfered: (data) => {},
            onConferenceCall: (data) => {},
            onLogout: () => {},
            onIncomingCallRinging: async (lineData) => {
                general.write_storage(lineData.lineData.index, null , "odoo_name")
                general.write_storage(lineData.lineData.index, false, "call_accepted_line")
                odooHelper.searchContactOrleads('res.partner',lineData.lineData.peer_number).then((data) => {
                    if(Array.isArray(data) && data.length>0) {
                        general.override_peername(lineData.lineData.index, data[0].name);
                        general.write_storage(lineData.lineData.index, {id: data[0].id , name: data[0].name, type: "Contact", isIncoming: true}, "odoo_name")
                    } else {
                        general.write_storage(lineData.lineData.index, {id: "" , name: "", type: "", isIncoming: true}, 'odoo_name')
                    }
                })
            },  
            onLineCountChange: async (data) => {
                odooHelper.click2dial(window)
                VenderDetails= null;
                VenderDetails = new checkVendor()
            },
            onLogin: (data) => {},
            onError: async (err) =>{},
            onConnectionEstablished: async (data) => {},
            onClosePBXEndpoint: async () => {},
            onGetPbxConnectors: async (data) => {},
            onGetProfile: async (data) => {},
            onPeerChanged: (data) => {},
            onCallTransfering: (data) => {},            
            setCrmData :  async (line, phoneNumber, data) => {
                let returnValue =  await general.add_tab_records({origin:[],tags:'contacts',model_name: 'res.partner',phone_number: phoneNumber, btntext: 'Create New Contact' })
                if(await odooHelper.is_leads_activated()) {
                    returnValue = await general.add_tab_records({origin:returnValue,tags:'leads',model_name: 'crm.lead',phone_number: phoneNumber, btntext: 'Create New Lead' })
                }
                return returnValue
            },
            onCrmDataClick: async(data) => {
                let lc = await general.read_storage(data.line, "odoo_name")
                let dataTypeSelected = document.querySelector('.tab-content > .active').classList.toString();
                if( dataTypeSelected.split('-').includes('leads')){
                    odooHelper.route_to({id: data.returnValue,name : "Leads",model:"crm.lead", view_type:"form"})
                    if(lc) {
                        Object.assign(lc,{id: data.returnValue, type: "Lead"})
                        odooHelper.open_view_dialog('crm.lead', data.returnValue)
                    }
                }
                if( dataTypeSelected.split('-').includes('contacts')){
                    odooHelper.route_to({id: data.returnValue,name : "Contact",model:"crm.lead", view_type:"form"})
                    if(lc) {
                        Object.assign(lc,{id: data.returnValue , type: "Contact"})
                        odooHelper.open_view_dialog('res.partner', data.returnValue)
                    }
                }
                general.write_storage(data.line, lc , "odoo_name")
            },
            onCrmButton: async (line, phoneNumber, data)=>{
                let btn =  document.querySelector('.tab-content > .active> .ringdesk-crm-btn') ;
                let model_name = "", tab_type =  ""
                if(btn!=null && btn.classList.contains('leads')) {
                    model_name = "crm.lead"
                    tab_type = "Lead"
                } else if(btn!=null && btn.classList.contains('contacts')) {
                    model_name = "res.partner"
                    tab_type = "Contact"
                }
                odooHelper.insert(model_name, {name: data.peer_name ? data.peer_name : data.peer_number, phone: data.peer_number}).then(result => {
                    //  odooHelper.route_to({id: result,name : tab_type ,model:model_name, view_type:"form"})
                    odooHelper.open_view_dialog(model_name, result)
                }).catch(err=>{
                    console.log(`Something wrong while creating ${tab_type.toString().toLowerCase()} ::`, err)
                    let dropdown =  document.querySelector(`[href = "ticket-dropdown-${parseInt(line)}"]`);
                    dropdown.click();
                })
            }
        }
    },
    styles: {
        mainBox: {},
        phoneNumberInput: {},
        phoneLines: {
            idle: {},
            dialing: {},
            calling: {},
            onHold: {}
        },
        callButton: {
            'background-color': '#1ac221',
            'border-color': '#1ac221',
            color: '#fff'
        },
        receiveCallButton: {},
        endCallButton: {},
        pauseButton: {},
        transferCallButton: {},
        redialButton: {},
        conferenceButton: {},
        volumeMuteButton: {},
        logoutButton: {},
        icons: {
            makeCallIcon: 'i-phone',
            receiveCallIcon: 'i-phone',
            transferCallIcon: 'i-loop',
            pauseCallIcon: 'i-pause',
            endCallIcon: 'i-phone-hang-up',
            dropdownIcon: 'i-keyboard_arrow_down',
            redialIcon: 'i-spinner11',
            conferenceCallIcon: 'i-users',
            volumeIcon: 'i-volume-high',
            muteIcon: 'i-volume-mute2',
            logoutIcon: 'i-exit'
        }
    }
});
   odooHelper.oauth_login(app_ringdesk)
})();

