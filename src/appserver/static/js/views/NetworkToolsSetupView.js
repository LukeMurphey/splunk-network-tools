
require.config({
    paths: {
        text: '../app/network_tools/js/lib/text',
        console: '../app/network_tools/js/lib/console'
    }
});

define([
    "underscore",
    "backbone",
    "splunkjs/mvc",
    "jquery",
    "splunkjs/mvc/simpleform/input/dropdown",
    "models/SplunkDBase",
    "collections/SplunkDsBase",
    "splunkjs/mvc/simplesplunkview",
    "text!../app/network_tools/js/templates/NetworkToolsSetupView.html",
    "util/splunkd_utils",
    "css!../app/network_tools/css/NetworkToolsSetupView.css"
], function(
    _,
    Backbone,
    mvc,
    $,
    DropdownInput,
    SplunkDBaseModel,
    SplunkDsBaseCollection,
    SimpleSplunkView,
    Template,
    splunkd_utils
){

	var Indexes = SplunkDsBaseCollection.extend({
	    url: "data/indexes",
	    initialize: function() {
	      SplunkDsBaseCollection.prototype.initialize.apply(this, arguments);
	    }
	});

	var AppConfig = SplunkDBaseModel.extend({
	    initialize: function() {
	    	SplunkDBaseModel.prototype.initialize.apply(this, arguments);
	    }
	});

    return SimpleSplunkView.extend({
        className: "NetworkToolsSetupView",

        events: {
            "click #save-config" : "saveConfig"
        },
        
        initialize: function() {

        	// Get the indexes
        	this.indexes = new Indexes();
        	this.indexes.on('reset', this.gotIndexes.bind(this), this);
        	
        	this.indexes.fetch({
                success: function() {
                  console.info("Successfully retrieved the list of indexes");
                },
                error: function() {
                  console.error("Unable to fetch the indexes");
                }
            });

            this.app_config = null;

            this.capabilities = null;
            this.is_using_free_license = null;
        },

        /**
         * Get the app configuration.
         */
        getAppConfig: function(){
	        this.app_config = new AppConfig();
	        	
            this.app_config.fetch({
                url: splunkd_utils.fullpath('/services/admin/network_tools/default'),
                success: function (model, response, options) {
                    console.info("Successfully retrieved the app configuration");

                    // Set the index setting
                    mvc.Components.getInstance("index").val(model.entry.associated.content.attributes.index);

                }.bind(this),
                error: function () {
                    console.warn("Unable to retrieve the app configuration");
                }.bind(this)
            });
        },

        /**
         * Show a message indicating success.
         */
        showSuccessMessage: function(message){
        	this.hideFailureMessage();
        	$("#success_text", this.$el).text(message);
        	$("#success_message", this.$el).show();
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
         * Save the configuration.
         */
        saveConfig: function(){

            // Modify the model
            this.app_config.entry.content.set({
                index: mvc.Components.getInstance("index").val()
            }, {
                silent: true
            });

            // Kick off the request to edit the entry
            var saveResponse = this.app_config.save();

            // Wire up a response to tell the user if this was a success
            if (saveResponse) {

                // Change the button to indicate a saving state
                this.$('.btn-primary').text('Saving Configuration...');
                this.$('.btn-primary').attr('disabled', '');

                // If successful, show a success message
                saveResponse.done(function(model, response, options){
                    this.showSuccessMessage("The changes were successfully saved");
                    this.$('.btn-primary').text('Save Configuration');
                    this.$('.btn-primary').attr('disabled', null);
                }.bind(this))

                // Otherwise, show a failure message
                .fail(function(response){
                    this.showFailureMessage("The changes could not be saved");
                    this.$('.btn-primary').text('Save Configuration');
                    this.$('.btn-primary').attr('disabled', null);
                }.bind(this));
            }

        },
        
        /**
         * Get the list of a collection model as choices.
         */
        getChoices: function(collection, filter_fx){
        	
        	// Make a default for the filter function
        	if(typeof filter_fx === 'undefined'){
        		filter_fx = null;
        	}
        	
        	// If we don't have the model yet, then just return an empty list for now
        	if(!collection){
        		return [];
        	}
        	
        	var choices = [];
        	
        	for(var c = 0; c < collection.models.length; c++){
        		
        		// Stop if the filtering function says not to include this entry
        		if(filter_fx && !filter_fx(collection.models[c].entry) ){
        			continue;
        		}
        		
        		// Otherwise, add the entry
        		choices.push({
        			'label': collection.models[c].entry.attributes.name,
        			'value': collection.models[c].entry.attributes.name
        		});
        	}
        	
        	return choices;
        	
        },

        /**
         * Get the indexes
         */
        gotIndexes: function(){
        	
        	// Update the list
        	if(mvc.Components.getInstance("index")){
        		mvc.Components.getInstance("index").settings.set("choices", this.getChoices(this.indexes, function(entry){
        			return !(entry.attributes.name[0] === "_");
        		}));
        	}
        	
        },

        /**
         * Determine if the user has the given capability.
         */
        hasCapability: function(capability){

        	var uri = Splunk.util.make_url("/splunkd/__raw/services/authentication/current-context?output_mode=json");

        	if(this.capabilities === null){

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

			// See if the user is running the free license
			if(this.capabilities.length === 0 && this.is_using_free_license === null){

				uri = Splunk.util.make_url("/splunkd/__raw/services/licenser/groups/Free?output_mode=json");

				// Do a call to see if the host is running the free license
	            jQuery.ajax({
	            	url:     uri,
	                type:    'GET',
	                async:   false,
	                success: function(result) {

	                	if(result !== undefined){
	                		this.is_using_free_license = result.entry[0].content['is_active'];
	                	}
						else{
							this.is_using_free_license = false;
						}

	                }.bind(this)
	            });
			}

			// Determine if the user should be considered as having access
			if(this.is_using_free_license){
				return true;
			}
			else{
				return $.inArray(capability, this.capabilities) >= 0;
			}

        },

        render: function () {

            this.getAppConfig();

        	var has_permission = this.hasCapability('admin_all_objects');
        	
        	this.$el.html(_.template(Template, {
        		'has_permission' : has_permission
        	}));
        	
        	// Make the indexes selection drop-down
            var indexes_dropdown = new DropdownInput({
                "id": "index",
                "selectFirstChoice": false,
                "showClearButton": true,
                "el": $('#inputIndexes', this.$el),
                "choices": this.getChoices(this.indexes)
            }, {tokens: true}).render();
        	
        }
    });
});