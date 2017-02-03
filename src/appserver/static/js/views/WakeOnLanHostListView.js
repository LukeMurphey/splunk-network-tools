
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
    "css!../app/network_tools/css/SplunkDataTables.css"
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
        	
        	// Get the hosts
            
        	if(KVStore && KVStore.Model){
        		this.getHosts();
        	}
        	
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
            "click create-host" : "createHost",
            "click edit-host" : "editHost"
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
        	var name = $(ev.target).data("name");
        	
        	// Perform the call
        	$.ajax({
        			url: splunkd_utils.fullpath(['/en-US/custom/network_tools/network_tools/wake'].join('/')),
        			data: {'host' : name},
        			type: 'POST',
        			
        			// On success, populate the table
        			success: function() {
        				console.info('Host wake-on-lan packet sent');
        			}.bind(this),
        		  
        			// Handle cases where the file could not be found or the user did not have permissions
        			complete: function(jqXHR, textStatus){
        				if( jqXHR.status == 403){
        					console.info('Inadequate permissions to wake host');
        				}
        				else{
        					this.retain_state = true;
        					// TODO put in a delay for this, to see if the host has awoken
        					//this.getHosts();
        				}
        				
        			}.bind(this),
        		  
        			// Handle errors
        			error: function(jqXHR, textStatus, errorThrown){
        				if( jqXHR.status != 403 ){
        					console.info('Host wake-on-lan packet request failed');
        				}
        			}.bind(this)
        	});
        	
        	return false;
        },
        
        /**
         * Delete the given host.
         */
        deleteHost: function(ev){
        	
        	// Get the input that is being requested to disable
        	var input = $(ev.target).data("name");
        	
        	var network_host_model = this.network_hosts_model.get(selected_key);
        	
        	// Remove the host
        	if(network_host_model !== null){
        		network_host_model.destroy({
        			success: function(model, response) {
        			  console.info("Host deleted");
        			  this.showMessage("Host successfully deleted");
        			  
        			  // Reload the view
        			  this.getHosts();
        			  
        			}.bind(this)
        		});
        	}
        	
        	
        },
        
        /**
         * Open a dialog to disable the input.
         */
        openDisableInputDialog: function(ev){
        	
        	// Get the input that is being requested to disable
        	var name = $(ev.target).data("name");
        	var namespace = $(ev.target).data("namespace");
        	var owner = $(ev.target).data("owner");
        	
        	// Record the info about the input to disable
        	$("#disable-this-input", this.$el).data("name", name);
        	$("#disable-this-input", this.$el).data("namespace", namespace);
        	$("#disable-this-input", this.$el).data("owner", owner);
        	
        	// Show the info about the input to disable
        	$(".disable-input-name", this.$el).text(name);
        	$(".disable-input-namespace", this.$el).text(namespace);
        	$(".disable-input-owner", this.$el).text(owner);
        	
        	// Show the modal
        	$("#disable-input-modal", this.$el).modal();
        	
        	return false;
        	
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
         * Get the description for the app name
         */
        getAppDescriptionFromName: function(name){
        	
    		for(var c = 0; c < this.apps.models.length; c++){
    			
    			if(this.apps.models[c].entry.attributes.name === name){
    				return this.apps.models[c].entry.associated.content.attributes.label;
    			}
    			
    		}
    		
    		return name;
        	
        },
        
        /**
         * Apply a filter to the table
         */
        applyFilter: function(){
        	
        	// Determine if we even need to apply this filter
        	var applied_filter_signature = ":" + this.filter_app + ":" + $('#free-text-filter').val();
        	
        	if(applied_filter_signature === this.applied_filter){
        		return;
        	}
        	
        	// Persist the signature for this filter
        	this.applied_filter = applied_filter_signature;
        	
        	// Get the app filter
        	if( this.filter_app !== null ){
        		this.data_table.columns(2).search( "^" + this.filter_app + "$", true );
        	}
        	else{
        		this.data_table.columns(2).search( "" );
        	}
        	
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
         * Get a count of the inputs that exist.
         */
        getInputsCount: function(){
        	var inputs = this.getInputsJSON();
        	
        	if(inputs){
        		return inputs.length;
        	}
        	else{
        		return 0;
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
        		'hosts_count' : this.network_hosts_model.models.length
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
                              { "searchable": false } // Actions
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