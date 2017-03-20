
require.config({
    paths: {
        datatables: '../app/network_tools/js/lib/DataTables/js/jquery.dataTables',
        bootstrapDataTables: '../app/network_tools/js/lib/DataTables/js/dataTables.bootstrap',
        text: '../app/network_tools/js/lib/text',
        console: '../app/network_tools/js/lib/console',
        kvstore: '../app/network_tools/contrib/kvstore'
    },
    shim: {
        'bootstrapDataTables': {
            deps: ['datatables']
        },
        'kvstore': {
	    	deps: ['jquery', 'backbone', 'underscore']
	    }
    }
});

define([
    "underscore",
    "backbone",
    "models/SplunkDBase",
    "collections/SplunkDsBase",
    "splunkjs/mvc",
    "jquery",
    "splunkjs/mvc/simplesplunkview",
    "text!../app/network_tools/js/templates/WakeOnLanHostListView.html",
    "bootstrapDataTables",
    "util/splunkd_utils",
    "kvstore",
    "bootstrap.dropdown",
    "css!../app/network_tools/css/WakeOnLanHostListView.css",
    "css!../app/network_tools/css/SplunkDataTables.css",
    "css!../app/network_tools/css/server.css"
], function(
    _,
    Backbone,
    SplunkDBaseModel,
    SplunkDsBaseCollection,
    mvc,
    $,
    SimpleSplunkView,
    Template,
    dataTable,
    splunkd_utils,
    KVStore
){
	
	// Initialize the KV store model
	if(KVStore && KVStore.Model){
		var NetworkHostModel = KVStore.Model.extend({
		    collectionName: 'network_hosts'
		});
		
		var NetworkHostCollection = KVStore.Collection.extend({
		    collectionName: 'network_hosts',
		    model: NetworkHostModel
		});
	
	}
	
    // Define the custom view class
    var WakeOnLanHostListView = SimpleSplunkView.extend({
        className: "WakeOnLanHostListView",
        
        defaults: {
        	change_dropdown_titles: true
        },
        
        /**
         * Initialize the class.
         */
        initialize: function() {
        	this.options = _.extend({}, this.defaults, this.options);
        	
        	// Save the options
        	this.change_dropdown_titles = this.options.change_dropdown_titles;
            
            // This tracks the filter that was applied
            this.applied_filter = null;
            
            // The reference to the data-table
            this.data_table = null;
            
            // This indicates if data-table's state should be retained
            this.retain_state = false;
            
            // This will contain the collection of hosts
            this.network_hosts_model = null;
            
            // This records the status of hosts (whether up or down)
        	this.hosts_statuses = {};
            
        	// Get the hosts
        	if(KVStore && KVStore.Model){
        		this.getHosts();
        	}
        	
        	// Keep a variable around to prevent more than one ping from running at a time
        	this.ping_running = false;
        	
        	// Start pinging the hosts to show whether they are online or not
        	this.update_host_id = 0;
        	setInterval(this.updateHostsStatuses.bind(this), 1000);
        	
        	// Setup an interval to hide the informational message if it should be hidden
        	this.message_posted_time = null;
        	setInterval(this.hideMessageIfNecessary.bind(this), 1000);
        	
        },
        
        events: {
        	
        	// Filtering
        	"click .app-filter > .dropdown-menu > li > a" : "onClickAppFilter",
        	"change #free-text-filter" : "applyFilter",
        	"keyup #free-text-filter" : "goFilter",
        	"keypress #free-text-filter" : "goFilter",
        	
        	// Options for deleting hosts
        	"click .delete-host" : "openDeleteHostDialog",
        	"click #delete-this-host" : "deleteHost",
        		
            // Options for waking hosts
            "click .wake-host" : "wakeHost",
            
            // Options for creating and editing hosts
            "click .create-host" : "openCreateHostDialog",
            "click .edit-host" : "openEditHostDialog",
            "click #save-host" : "saveHost",
            
            // This is used to fix some wierdness with bootstrap and input focus
            "shown #add-host-modal" : "focusView",
            
            // Get the inputs to trigger validation when the user moves to the next input
            "change #inputName" : "validateName",
            "change #inputMAC" : "validateMACAddress",
            "change #inputIP" : "validateIPAddress",
            "change #inputPort" : "validatePort"
        },
            	        
        /**
         * Fixes an issue where clicking an input loses focus instantly due to a problem in Bootstrap.
         * 
         * http://stackoverflow.com/questions/11634809/twitter-bootstrap-focus-on-textarea-inside-a-modal-on-click
         */
        focusView: function(){
        	$('#inputName').focus();
        },
        
        /**
         * Populate the list of hosts.
         */
        gotHosts: function(){
        	this.renderList();
        },
        
        /**
         * Get the hosts
         */
        getHosts: function(){
        	
        	this.network_hosts_model = new NetworkHostCollection();
        	this.network_hosts_model.on('reset', this.gotHosts.bind(this), this);
        	
        	// Start the loading of the hosts
        	this.network_hosts_model.fetch({
                success: function() {
                  console.info("Successfully retrieved the list of hosts");
                },
                error: function() {
                  console.error("Unable to fetch the hosts");
                }.bind(this),
                complete: function(jqXHR, textStatus){
                	if( jqXHR.status == 404){
                		// We don't support saved hosts (no KV support)
                		// TODO insert error message
                	}
                }.bind(this)
            }).done(function() { this.gotHosts(); }.bind(this));
        },
        
        /**
         * Set the name associated with the filter
         */
        setFilterText: function(filter_name, prefix, appendix){
        	
        	if (typeof appendix === "undefined") {
        		appendix = "All";
        	}
        	
    		if(this.change_dropdown_titles){
    			
    			if(appendix){
    				$("." + filter_name + " > .dropdown-toggle").html(prefix + ': ' + appendix + '<span class="caret"></span>');
    			}
    			else{
    				$("." + filter_name + " > .dropdown-toggle").html(prefix + '<span class="caret"></span>');
    			}
    			
    		}
        },
        
        /**
         * Perform the operation to perform a filter.
         */
        doFilter: function(filter_name, prefix, value, apply_filter){
        	
        	// Load a default for the apply_filter parameter
        	if( typeof apply_filter == 'undefined' ){
        		apply_filter = true;
        	}
        	
        	// Determine the value that should be checked
        	var valueToSet = value;
        	
        	if(value === null){
        		valueToSet = "All";
        	}
        	
        	// Set the text of the filter dropdown
        	this.setFilterText(filter_name, prefix, valueToSet);
        	
        	// Show the checked icon on the selected entry and only on that entry
        	$('.' + filter_name + ' > .dropdown-menu > li > a').each(function() {
        		if($(this).text() === valueToSet){
        			$("i", this).removeClass('hide');
        		}
        		else{
        			$("i", this).addClass('hide');
        		}
        	});
        	
        	// Apply the filter to the results
        	if(apply_filter){
        		this.applyFilter();
        	}
        	
        },
        
        /**
         * Wake the given host. 
         */
        wakeHost: function(ev){
        	
        	// Get the host to wake
        	var _key = $(ev.target).data("key");
        	
        	// Get the model in case we need it
        	var host = this.network_hosts_model.get(_key);
        	var name = host.attributes.name;
        	
        	// Perform the call
        	$.ajax({
        			url: splunkd_utils.fullpath(['/en-US/custom/network_tools/network_tools/wake'].join('/')),
        			data: {'host' : name},
        			type: 'POST',
        			
        			// On success, populate the table
        			success: function() {
        				console.info('Host wake-on-lan packet sent');
        				this.showSuccessMessage('Wake-on-lan request sent to host');
        			}.bind(this),
        		  
        			// Handle cases where the file could not be found or the user did not have permissions
        			complete: function(jqXHR, textStatus){
        				if( jqXHR.status == 403){
        					console.info('Inadequate permissions to wake host');
        					this.showFailureMessage('Inadequate permissions to send a wake-on-lan request');
        				}
        				else{
        					this.retain_state = true;
        					// TODO put in a delay for this, to see if the host has awoken
        					//this.getHosts();
        					//this.updateHostStatus(host.attributes.ip_address);
        				}
        				
        			}.bind(this),
        		  
        			// Handle errors
        			error: function(jqXHR, textStatus, errorThrown){
        				if( jqXHR.status != 403 ){
        					console.info('Host wake-on-lan packet request failed');
        					this.showFailureMessage('Error when attempting to send a wake-on-lan request');
        				}
        			}.bind(this)
        	});
        	
        	return false;
        },
        
        /**
         * Open the host creation dialog.
         */
        openCreateHostDialog: function(){
        	
        	// Set the form values
  		  	$("#inputName", this.$el).val("");
  		  	$("#inputIP", this.$el).val("");
  		  	$("#inputMAC", this.$el).val("");
  		  	$("#inputPort", this.$el).val("");
  		  	$("#inputKey", this.$el).val("");
  		  	
			// Clear the validation state
			this.clearAllValidators();

  		  	// Open the modal dialog
        	$("#add-host-modal", this.$el).modal();
        },
        
        /**
         * Save the given host
         */
        saveHost: function(){
        	
        	// Stop if the input doesn't validate
        	if(!this.validateHostForm()){
        		return;
        	}
        	
        	// Get the key of the item we are editing
        	var _key =  $("#inputKey", this.$el).val();
        	
        	// Get the values
  		  	var name = $("#inputName", this.$el).val();
  		  	var ip_address = $("#inputIP", this.$el).val();
  		  	var mac_address = $("#inputMAC", this.$el).val();
  		  	var port = $("#inputPort", this.$el).val();
        	
  		  	// This will include the entry that is saved
  		  	var host = null;
  		  	
        	// Make a new entry
            if (_key === "" || _key === null) {
        	
            	// Make the host
	        	host = new NetworkHostModel({
	        		  name: name,
	        		  ip_address: ip_address,
	        		  mac_address: mac_address,
	        		  port: port
	        	});
	
	        	// Save the host and update the list
	        	host.save().done(function(){
	        		this.showSuccessMessage("Host successfully created");
	        		$("#add-host-modal", this.$el).modal('hide');
	        		this.getHosts();
	        	}.bind(this))
	        	
            }
            
            // Edit the existing entry
            else{
            	
            	// Find the entry
            	host = this.network_hosts_model.get(_key);
            	
            	// Update the entry
            	host.set({
	        		  name: name,
	        		  ip_address: ip_address,
	        		  mac_address: mac_address,
	        		  port: port
	        	});
            	
            	host.save().done(function(){
            		$("#add-host-modal", this.$el).modal('hide');
            		this.renderList(true);
            		
            		this.showSuccessMessage("Host successfully saved");
            	}.bind(this));

            }
        },
        
        /**
         * Open the host creation dialog for editing.
         */
        openEditHostDialog: function(ev){
        	
        	// Get the key of the item we are editing
        	var _key = $(ev.target).data("key");
        	
        	var host = this.network_hosts_model.get(_key);
        	
        	if(host === null){
        		alert("Unable to find the host to edit");
        		return;
        	}
        	
        	// Set the form values
  		  	$("#inputName", this.$el).val(host.attributes.name);
  		  	$("#inputIP", this.$el).val(host.attributes.ip_address);
  		  	$("#inputMAC", this.$el).val(host.attributes.mac_address);
  		  	$("#inputPort", this.$el).val(host.attributes.port);
  		  	$("#inputKey", this.$el).val(host.attributes._key);
  		  	
        	// Show the modal
        	$("#add-host-modal", this.$el).modal();
        },
        
        /**
         * Determine if the provided MAC address is valid.
         */
        isValidMACAddress: function(mac_address){
        	var regex = /^[0-9a-f]{1,2}([\.:-])(?:[0-9a-f]{1,2}\1){4}[0-9a-f]{1,2}$/gmi;
        	
        	return regex.test(mac_address);
        },
        
        /**
         * Determine if the provided IP address is valid.
         */
        isValidIPAddress: function(ip_address){
        	
        	if(ip_address === ""){
        		return true;
        	}
        	
        	var regex = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        	
        	return regex.test(ip_address);
        },
        
        /**
         * Determine if the provided port is valid.
         */
        isValidPort: function(port){
        	
        	if(port === ""){
        		return true;
        	}
        	
        	var regex = /^[0-9]+$/;
        	
        	return regex.test(port);
        },
        
        /**
         * Determine if the provided name is valid.
         */
        isValidName: function(name){
        	var regex = /^.+$/;
        	
        	return regex.test(name);
        },
        
        /**
         * Perform validation and show/hide error messages accordingly.
         */
        doValidation: function(selector, value, validation_fx, message){
        	if(!validation_fx(value)){
  		  		$(selector, this.$el).addClass('error');
  		  		$(selector + ' .help-inline', this.$el).text(message);
  		  		return 1;
  		  	}
  		  	else{
  		  		this.clearValidationState(selector);
  		  		return 0;
  		  	}
        },
        
		/**
		 * Clear the validation state for the given input.
		 */
		clearValidationState: function(selector){
  		  	$(selector, this.$el).removeClass('error');
  		  	$(selector + ' .help-inline', this.$el).text('');
		},

		/**
		 * Clear the validation state for all of the forms.
		 */
		clearAllValidators: function(){
			this.clearValidationState('.input-host-name.control-group');
			this.clearValidationState('.input-host-mac.control-group');
			this.clearValidationState('.input-host-ip.control-group');
			this.clearValidationState('.input-host-port.control-group');
		},

        /**
         * Validate the name field and post a message accordingly.
         */
        validateName: function(){
        	return this.doValidation('.input-host-name.control-group', $("#inputName", this.$el).val(), this.isValidName.bind(this), 'Name is not valid');
        },
        
        /**
         * Validate the MAC address field and post a message accordingly.
         */
        validateMACAddress: function(){
        	return this.doValidation('.input-host-mac.control-group', $("#inputMAC", this.$el).val(), this.isValidMACAddress.bind(this), 'A valid MAC address must be provided (like 00:11:22:33:44:55)');
        },
        
        /**
         * Validate the IP address field and post a message accordingly.
         */
        validateIPAddress: function(){
        	return this.doValidation('.input-host-ip.control-group', $("#inputIP", this.$el).val(), this.isValidIPAddress.bind(this), 'IP address is invalid')
        },
        
        /**
         * Validate the port field and post a message accordingly.
         */
        validatePort: function(){
        	return this.doValidation('.input-host-port.control-group', $("#inputPort", this.$el).val(), this.isValidPort.bind(this), 'Port is invalid')
        },
        
        /**
         * Determine if the form is valid.
         */
        validateHostForm: function(){
        	
        	var issues = 0;
        	
        	// Get the values
  		  	var name = $("#inputName", this.$el).val();
  		  	var ip_address = $("#inputIP", this.$el).val();
  		  	var mac_address = $("#inputMAC", this.$el).val();
  		  	var port = $("#inputPort", this.$el).val();
  		  	
  		  	// Test 'em
  		  	issues += this.validateName();
  		  	issues += this.validateMACAddress();
  		  	issues += this.validateIPAddress();
  		  	issues += this.validatePort();
        	
  		  	// Return the validation status
  		  	if(issues > 0){
  		  		return false;
  		  	}
  		  	else{
  		  		return true;
  		  	}
        },
        
        /**
         * Delete the given host.
         */
        deleteHost: function(ev){
        	
        	// Get the input that is being requested to disable
        	var _key = $(ev.target).data("key");
        	
        	var network_host_model = this.network_hosts_model.get(_key);
        	
        	// Remove the host
        	if(network_host_model !== null){
        		network_host_model.destroy({
        			success: function(model, response) {
        			  console.info("Host deleted");
        			  this.showSuccessMessage("Host successfully deleted");
        			  
        			  // Reload the view
        			  this.getHosts();
        			  
        			}.bind(this)
        		});
        	}
        	
        },
        
        /**
         * Open a dialog to delete a host.
         */
        openDeleteHostDialog: function(ev){
        	
        	// Get the host that is being requested to delete
        	var _key = $(ev.target).data("key");
        	var network_host_model = this.network_hosts_model.get(_key);
        	
        	// Record the info about the host to delete
        	$("#delete-this-host", this.$el).data("key", _key);
        	
        	// Show the info about the input to delete
        	$(".delete-host-name", this.$el).text(network_host_model.attributes.name);
        	
        	// Show the modal
        	$("#remove-host-modal", this.$el).modal();
        	
        	return false;
        	
        },
        
        /**
         * Hide the message if it is old enough
         */
        hideMessageIfNecessary: function(){
        	if(this.message_posted_time && ((this.message_posted_time + 5000) < new Date().getTime() )){
        		this.message_posted_time = null;
        		$("#success_message", this.$el).fadeOut(200);
        	}
        },
        
        /**
         * Show a message indicating success.
         */
        showSuccessMessage: function(message){
        	this.hideFailureMessage();
        	$("#success_text", this.$el).text(message);
        	$("#success_message", this.$el).show();
        	this.message_posted_time = new Date().getTime();
        },
        
        /**
         * Hide the success message.
         */
        hideSuccessMessage: function(message){
        	$("#success_message", this.$el).hide();
        },
        
        /**
         * Show a message indicating failure.
         */
        showFailureMessage: function(message){
        	this.hideSuccessMessage();
        	$("#error_text", this.$el).text(message);
        	$("#failure_message", this.$el).show();
        },
        
        /**
         * Hide the success failure.
         */
        hideFailureMessage: function(message){
        	$("#failure_message", this.$el).hide();
        },
        
        /**
         * Apply a filter to the table
         */
        goFilter: function(ev){
        	
        	var code = ev.keyCode || ev.which;
        	
            if (code == 13){
            	ev.preventDefault();
            }
        	
        	this.applyFilter();
        },
        
        /**
         * Apply a filter to the table
         */
        applyFilter: function(){
        	
        	// Determine if we even need to apply this filter
        	var applied_filter_signature = $('#free-text-filter').val();
        	
        	if(applied_filter_signature === this.applied_filter){
        		return;
        	}
        	
        	// Persist the signature for this filter
        	this.applied_filter = applied_filter_signature;
        	
        	// Apply the text filter
        	this.filter_text = $('#free-text-filter').val();
        	this.data_table.search( $('#free-text-filter').val() ).draw();
        },
        
        /**
         * Determine if the string end with a sub-string.
         */
        endsWith: function(str, suffix) {
            return str.indexOf(suffix, str.length - suffix.length) !== -1;
        },
        
        /**
         * Perform a ping to see if the host is online and update the icon appropriately.
         */
        updateHostStatus: function(ip_address){
        	
        	// Make sure that the host has an IP address
        	if(!ip_address || ip_address === ""){
        		return;
        	}
        	
			// See if there is an entry for this host already. We need to do this in order to make sure we record that we pinged it.
			var host_entry = this.hosts_statuses[ip_address];
			
			// If there isn't an entry, make one
			if(host_entry === undefined){
				host_entry = {
						'last_checked': (new Date).getTime(),
						'online': null
				};
				
				this.hosts_statuses[ip_address] = host_entry;
			}
			
			// Note that a ping is running
			this.ping_running = true;
			
			console.info("Pinging host: " + ip_address);
			
        	// Perform the call
        	$.ajax({
        			url: splunkd_utils.fullpath(['/en-US/custom/network_tools/network_tools/ping'].join('/')),
        			data: {'host' : ip_address},
        			type: 'POST',
        			
        			// On success, populate the table
        			success: function(data) {
        				
        				// Evaluate the result
        				if(data['return_code'] == 0){
        					host_entry['online'] = true;
        					$("[data-host='" + ip_address + "']").removeClass('host-unknown')
        						.removeClass('host-offline')
        						.removeClass('fade-offline')
        						.addClass('fade-online')
        						.addClass('host-online');
        				}
        				else{
        					host_entry['online'] = false;
        					$("[data-host='" + ip_address + "']").removeClass('host-unknown')
        						.addClass('host-offline')
        						.addClass('fade-offline')
        						.removeClass('fade-online')
        						.removeClass('host-online');
        				}
        				
        			}.bind(this),
        			
        			// Handle errors
        			error: function(jqXHR, textStatus, errorThrown){
        				if( jqXHR.status != 403 ){
        					
        				}
        			}.bind(this),
        			
        			complete: function(){
        				// Note when we successfully checked this host
        				host_entry['last_checked'] = (new Date).getTime();
        				this.ping_running = false;
        			}.bind(this)
        	});
        },
        
        /**
         * Perform the necessary pings to see which hosts are up.
         */
        updateHostsStatuses: function(){
        	
        	// Loop through the hosts and see if any need to be pinged
        	var keep_going = true;
        	
        	for(var c=0; c < this.network_hosts_model.models.length && keep_going; c++){
        		
        		// If we got through all of them, then loop around
        		if(this.update_host_id >= this.network_hosts_model.models.length){
        			this.update_host_id = 0;
        		}
        		
        		// Stop if a ping is running
        		if(this.ping_running){
        			break;
        		}
        		
        		// Find the status entry for the host
        		var host_entry = this.hosts_statuses[this.network_hosts_model.models[this.update_host_id].attributes.ip_address];
        		
        		// See if the host needs to be pinged
        		if(host_entry !== undefined && ((new Date).getTime() - host_entry.last_checked) < 20000){
        			continue; // This host does not need to be pinged
        		}
        		else{
        			// Start a ping for this host
            		this.updateHostStatus(this.network_hosts_model.models[this.update_host_id].attributes.ip_address);
            		keep_going = false;
        		}
        		
        		// Move to the next host
        		this.update_host_id += 1;
        		
        	}
        },
        
        /**
         * Determine if the host is online or not.
         */
        getHostOnlineStatusClass: function(host){
        	
        	// Determine the IP associated with the host
        	if(!host.attributes.ip_address || host.attributes.ip_address.length == 0 || this.hosts_statuses === undefined){
        		return "host-unknown";
        	}
        	
        	// Get the host status
        	var host_entry = this.hosts_statuses[host.attributes.ip_address];
        	
        	if(host_entry === undefined || host_entry['online'] === undefined){
        		return "host-unknown";
        	}
        	else if(host_entry['online']){
        		return "host-online";
        	}
        	else{
        		return "host-offline";
        	}
        	
        },
        
        /**
         * Render the list.
         */
        renderList: function(retainState){
        	
        	// Load a default for the retainState parameter
        	if( typeof retainState == 'undefined' ){
        		retainState = this.retain_state;
        	}
        	
        	// Get the template
            var input_list_template = $('#list-template', this.$el).text();
            
        	$('#content', this.$el).html(_.template(input_list_template, {
        		'hosts' : this.network_hosts_model.models,
        		'filter_text': this.filter_text,
        		'hosts_count' : this.network_hosts_model.models.length,
        		'getHostOnlineStatusClass' : this.getHostOnlineStatusClass.bind(this)
        	}));
        	
            // Make the table filterable, sortable and paginated with data-tables
            this.data_table = $('#table', this.$el).DataTable( {
                "iDisplayLength": 25,
                "bLengthChange": false,
                "searching": true,
                "aLengthMenu": [[ 25, 50, 100, -1], [25, 50, 100, "All"]],
                "bStateSave": true,
                "fnStateLoadParams": function (oSettings, oData) {
                	return retainState;
                },
                "aaSorting": [[ 1, "asc" ]],
                "aoColumns": [
                              null,                   // Name
                              null,                   // IP Address
                              { "searchable": false },// MAC Address
                              { "searchable": false, "sortable": false } // Actions
                            ]
            } );
        },
        
        /**
         * Render the page.
         */
        render: function () {
        	this.$el.html(Template);
        }
    });
    
    return WakeOnLanHostListView;
});