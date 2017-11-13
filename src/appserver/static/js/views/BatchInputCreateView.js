
require.config({
    paths: {
        "text": "../app/network_tools/js/lib/text",
        "bootstrap-tags-input": "../app/network_tools/js/lib/bootstrap-tagsinput.min"
    },
    shim: {
        'bootstrap-tags-input': {
        	deps: ['jquery']
        }
    }
});

define([
    "underscore",
    "backbone",
    "splunkjs/mvc",
    "util/splunkd_utils",
    "jquery",
    "splunkjs/mvc/simplesplunkview",
	"models/services/server/ServerInfo",
    'text!../app/network_tools/js/templates/BatchInputCreateView.html',
    "bootstrap-tags-input",
    "splunk.util",
    "css!../app/network_tools/css/BatchInputCreateView.css",
    "css!../app/network_tools/js/lib/bootstrap-tagsinput.css"
], function(
    _,
    Backbone,
    mvc,
    splunkd_utils,
    $,
    SimpleSplunkView,
	ServerInfo,
    Template
){
    // Define the custom view class
    var BatchInputCreateView = SimpleSplunkView.extend({
        className: "BatchInputCreateView",
        
        defaults: {
        	
        },
        
        events: {
        	"click .create-inputs" : "doCreateInputs",
        	"click .stop-creating-inputs" : "stopCreateInputs"
        },
        
        initialize: function() {
        	this.options = _.extend({}, this.defaults, this.options);
        	
        	// These are internal variables
        	this.processing_queue = [];
        	this.processed_queue = [];
        	this.unprocessed_queue = [];
        	this.interval = null;
        	this.index = null;
        	this.dont_duplicate = true;
        	this.stop_processing = false;
        	this.capabilities = null;
        	this.inputs = null;
        	this.existing_input_names = [];
        	
        	this.getExistingInputs();
        },
        
        /**
         * Generate a suggested stanza from the host.
         */
        generateStanza: function(host, existing_stanzas){
        	// Set a default value for the existing_stanzas argument
        	if( typeof existing_stanzas == 'undefined' || existing_stanzas === null){
        		existing_stanzas = [];
        	}
        	
        	// If we have no existing stanzas, then just make up a name and go with it
        	if(existing_stanzas.length === 0){
            	return host;
        	}
        	
        	var possible_stanza = host;
        	var stanza_suffix_offset = 0;
        	var collision_found = false;
        	
        	while(true){
        		collision_found = false;
        		
        		// See if we have a collision
            	for(var c = 0; c < existing_stanzas.length; c++){
            		if(existing_stanzas[c] === possible_stanza){
            			collision_found = true;
            			break;
            		}
            	}
        		
            	// Stop if we don't have a collision
            	if(!collision_found){
            		return possible_stanza;
            	}
            	
            	// We have a collision, continue
            	else{
            		stanza_suffix_offset = stanza_suffix_offset + 1;
            		possible_stanza = stanza_base + "_" + stanza_suffix_offset;
            	}   		
        	}
        },
        
        /**
         * Create an input
         */
        createInput: function(dest, interval, index, count, name){
        	
        	// Get a promise ready
        	var promise = jQuery.Deferred();
        	
        	// Set a default value for the arguments
        	if( typeof name == 'undefined' ){
        		name = null;
        	}
        	
        	if( typeof count == 'undefined' ){
        		count = 1;
        	}
        	
        	if( typeof index == 'undefined' ){
        		index = null;
        	}
        	
        	// Populate defaults for the arguments
        	if(name === null){
        		name = this.generateStanza(dest, this.existing_input_names);
        	}
        	
        	// Make the data that will be posted to the server
        	var data = {
        		"dest": dest,
        		"interval": interval,
        		"name": name,
        		"runs": count,
        	};
        	
        	if(index !== null){
        		data["index"] = index;
        	}
        	
        	// Perform the call
        	$.ajax({
        			url: splunkd_utils.fullpath("/servicesNS/" + Splunk.util.getConfigValue("USERNAME") +  "/network_tools/data/inputs/ping?output_mode=json"),
        			data: data,
        			type: 'POST',
        			
        			// On success
        			success: function(data) {
        				console.info('Input created');
        				
        				// Remember that we processed this one
        				this.processed_queue.push(dest);
        				
        				// Make sure that we add the name so that we can detect duplicated names
        				this.existing_input_names.push(name);
        				
        			}.bind(this),
        		  
        			// On complete
        			complete: function(jqXHR, textStatus){
        				
        				// Handle cases where the input already existing or the user did not have permissions
        				if( jqXHR.status == 403){
        					console.info('Inadequate permissions');
        					this.showWarningMessage("You do not have permission to make inputs");
        				}
        				else if( jqXHR.status == 409){
        					console.info('Input already exists, skipping this one');
        				}
        				
        				promise.resolve();
        			  
        			}.bind(this),
        		  
        			// On error
        			error: function(jqXHR, textStatus, errorThrown){
        				
        				// These responses indicate that the user doesn't have permission of the input already exists
        				if( jqXHR.status != 403 && jqXHR.status != 409 ){
        					console.info('Input creation failed');
        				}
    					
    					// Remember that we couldn't process this on
    					this.unprocessed_queue.push(dest);
    					
        			}.bind(this)
        	});
        	
        	return promise;
        },
        
        /**
         * Keep on processing the inputs in the queue.
         */
        createNextInput: function(){
        	
        	// Stop if we are asked to
        	if(this.stop_processing){
        		return;
        	}
        	
        	// Update the progress bar
        	var progress = 100 * ((this.processed_queue.length + this.unprocessed_queue.length) / (this.processing_queue.length + this.processed_queue.length + this.unprocessed_queue.length));
        	$(".bar", this.$el).css("width", progress + "%");
        	
        	// Stop if we are done
        	if(this.processing_queue.length === 0){
        		
				if(this.processed_queue.length > 0){
					// Show a message noting that we are done
					this.showInfoMessage("Done creating the inputs (" + this.processed_queue.length + " created)");
				}
        		
        		var extra_message = "";
        		
        		if(this.dont_duplicate){
        			extra_message = " (duplicates are being skipped)";
        		}
        		
        		if(this.unprocessed_queue.length === 1){
        			this.showWarningMessage("1 input was not created" + extra_message);
        		}
        		else if(this.unprocessed_queue.length > 0){
        			this.showWarningMessage("" + this.unprocessed_queue.length + " inputs were not created" + extra_message);
        		}
        		
        		// Hide the dialog
        		$("#progress-modal", this.$el).modal('hide');
        		
        		// Clear the inputs we successfully created
				for(var c = 0; c < this.processed_queue.length; c++){
					$("#hosts", this.$el).tagsinput('remove', this.processed_queue[c]);
				}
        	}
        	
        	// Otherwise, keep going
        	else{
        		
        		// Get the next entry
        		var host = this.processing_queue.pop();
        		
        		// Make sure this host doesn't already exist, skip it if necessary
        		if(this.dont_duplicate && this.isAlreadyMonitored(host)){
        			$("#hosts", this.$el).tagsinput('remove', host);
        			this.unprocessed_queue.push(host);
        			console.info("Skipping creation of an input that already existed for " + host);
        			this.createNextInput();
        		}
        		
        		// Create the input
        		else{
                	// Process the next input
                    $.when(this.createInput(host, this.interval, this.index, 1)).done(function(){
                    	this.createNextInput();
              		}.bind(this));
        		}

        		
        	}
        },
        
        /**
         * Validate the inputs.
         */
        validate: function(){
        	
        	var issues = 0;
        	
        	// Validate the hosts
        	if($("#hosts", this.$el).tagsinput('items').length === 0){
        		issues = issues + 1;
        		$(".control-group.hosts", this.$el).addClass("error");
        		$(".control-group.hosts .help-inline", this.$el).show();
        	}
        	else{
        		$(".control-group.hosts", this.$el).removeClass("error");
        		$(".control-group.hosts .help-inline", this.$el).hide();
        	}
        	
        	// Validate the interval
        	if(!this.isValidInterval($("#interval", this.$el).val())){
        		issues = issues + 1;
        		$(".control-group.interval", this.$el).addClass("error");
        		$(".control-group.interval .help-inline", this.$el).show();
        	}
        	else{
           		$(".control-group.interval", this.$el).removeClass("error");
        		$(".control-group.interval .help-inline", this.$el).hide();
        	}
        	
        	return issues === 0;
        },
        
        /**
         * Returns true if the item is a valid interval.
         */
        isValidInterval: function(interval){
        	
        	var re = /^\s*([0-9]+([.][0-9]+)?)\s*([dhms])?\s*$/gi;
        	
        	if(re.exec(interval)){
        		return true;
        	}
        	else{
        		return false;
        	}
        },
        
        /**
         * Ensure that the tag is a valid host.
         */
        validateHost: function(event) {
        	
        	// Stop if the entry is blank
        	if(event.item.length === 0){
				this.showWarningMessage("Blank host not allowed");
				event.cancel = true;
			}

			// See if this is a valid CIDR, IP or hostname
			valid_regexs = [
				// CIDR: https://www.regexpal.com/93987
				/^([0-9]{1,3}\.){3}[0-9]{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$/,

				// IP, hostnames: http://jsfiddle.net/DanielD/8S4nq/
				/((^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$))|(^\s*((?=.{1,255}$)(?=.*[A-Za-z].*)[0-9A-Za-z](?:(?:[0-9A-Za-z]|\b-){0,61}[0-9A-Za-z])?(?:\.[0-9A-Za-z](?:(?:[0-9A-Za-z]|\b-){0,61}[0-9A-Za-z])?)*)\s*$)/
			];

			// See if any of the regexes matched
			var matched = false;
			for(var c = 0; c < valid_regexs.length; c++){
				if(valid_regexs[c].test(event.item)){
					matched = true;
				}
			}

			// If none matched, then reject the input
			if(!matched){
				event.cancel = true;
			}

        },
        
        /**
         * Stop creating the inputs.
         */
        stopCreateInputs: function(){
        	this.stop_processing = true;
        },
        
        /**
         * Create the inputs based on the inputs.
         */
        doCreateInputs: function(){
        	
        	if(this.validate()){
            	
            	this.hideMessages();
            	
            	this.processed_queue = [];
            	this.unprocessed_queue = [];
            	this.processing_queue = $("#hosts", this.$el).tagsinput('items');
            	this.interval = $("#interval", this.$el).val();
            	this.dont_duplicate = $(".dont-duplicate", this.$el).is(':checked');
            	//this.index = $("#index", this.$el).val();
            	
            	// Open the progress dialog
            	this.stop_processing = false;
            	$("#progress-modal", this.$el).modal();
            	
            	// Start the process
            	this.createNextInput();
        	}
        	
        },
        
        /**
         * Hide the given item while retaining the display value
         */
        hide: function(selector){
        	selector.css("display", "none");
        	selector.addClass("hide");
        },
        
        /**
         * Un-hide the given item.
         * 
         * Note: this removes all custom styles applied directly to the element.
         */
        unhide: function(selector){
        	selector.removeClass("hide");
        	selector.removeAttr("style");
        },
        
        /**
         * Hide the messages.
         */
        hideMessages: function(){
        	this.hideWarningMessage();
        	this.hideInfoMessage();
        },
        
        /**
         * Hide the warning message.
         */
        hideWarningMessage: function(){
        	this.hide($("#warning-message", this.$el));
        },
        
        /**
         * Hide the informational message
         */
        hideInfoMessage: function(){
        	this.hide($("#info-message", this.$el));
        },
        
        /**
         * Show a warning noting that something bad happened.
         */
        showWarningMessage: function(message){
        	$("#warning-message > .message", this.$el).text(message);
        	this.unhide($("#warning-message", this.$el));
        },
        
        /**
         * Show a warning noting that something bad happened.
         */
        showInfoMessage: function(message){
        	$("#info-message > .message", this.$el).text(message);
        	this.unhide($("#info-message", this.$el));
        },
        
        /**
         * Determine if the user has the given capability.
         */
        hasCapability: function(capability){

        	var uri = Splunk.util.make_url("/splunkd/__raw/services/authentication/current-context?output_mode=json");

        	if( this.capabilities === null ){

	            // Fire off the request
	            jQuery.ajax({
	            	url:     uri,
	                type:    'GET',
	                async:   false,
	                success: function(result) {
	                	if(result !== undefined){
	                		this.capabilities = result.entry[0].content.capabilities;
	                	}
	                }.bind(this)
	            });
        	}

            return $.inArray(capability, this.capabilities) >= 0;

        },
        
        /**
         * Determine if the given destination is already monitored.
         */
        isAlreadyMonitored: function(dest){
        	
        	for(var c = 0; c < this.inputs.length; c++){
        		
        		if(this.inputs[c].content.dest === dest){
        			return true;
        		}
        		
        	}
        	
        	return false;
        },
        
        /**
         * Get a list of the existing inputs.
         */
        getExistingInputs: function(){

        	var uri = splunkd_utils.fullpath("/servicesNS/nobody/search/data/inputs/ping?output_mode=json");

	        // Fire off the request
        	jQuery.ajax({
        		url: uri,
        		type: 'GET',
        		async: false,
        		success: function(result) {
        			if(result !== undefined){
        				this.inputs = result.entry;
        			}
        			
        			// Populate a list of the existing input names
        			this.existing_input_names = [];
        			
                	for(var c = 0; c < this.inputs.length; c++){
                		this.existing_input_names.push(this.inputs[c].name);
                	}

        		}.bind(this)
        	});

        },
        
        /**
         * Render the view.
         */
        render: function () {
			// Below is the list of capabilities required
			var capabilities_required = ['edit_modinput_ping', 'edit_tcp', 'list_inputs'];

			// Find out which capabilities are missing
			var capabilities_missing = [];

			// Check each one
			for (var c = 0; c < capabilities_required.length; c++) {
				if (!this.hasCapability(capabilities_required[c])) {
					capabilities_missing.push(capabilities_required[c]);
				}
			}

			// Render the view
			this.$el.html(_.template(Template, {
				'has_permission': capabilities_missing.length === 0,
				'capabilities_missing': capabilities_missing
			}));

			// Render the hosts as tags
			$("#hosts").tagsinput('items');

			$("#hosts").on('beforeItemAdd', this.validateHost.bind(this));
        }
    });
    
    return BatchInputCreateView;
});