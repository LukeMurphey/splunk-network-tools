
require.config({
    paths: {
        text: '../app/network_tools/js/lib/text',
        console: '../app/network_tools/js/lib/console',
        setup_view: '../app/network_tools/js/views/SetupView'
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
    "setup_view",
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
    SetupView,
    Template,
    splunkd_utils
){

	var Indexes = SplunkDsBaseCollection.extend({
	    url: "data/indexes",
	    initialize: function() {
	      SplunkDsBaseCollection.prototype.initialize.apply(this, arguments);
	    }
	});

	var NetworkToolsConfig = SplunkDBaseModel.extend({
	    initialize: function() {
	    	SplunkDBaseModel.prototype.initialize.apply(this, arguments);
	    }
	});

    return SetupView.extend({
        className: "NetworkToolsSetupView",

        events: {
            "click #save-config" : "saveConfig"
        },
        
        defaults: {
        	app_name: "network_tools"
        },

        initialize: function() {

            // Merge the provided options and the defaults
        	this.options = _.extend({}, this.defaults, this.options);

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

            //this.app_name
            SetupView.prototype.initialize.apply(this, [this.options]);
        },

        /**
         * Get the app configuration.
         */
        getNetworkToolsConfig: function(){
	        this.network_tools_config = new NetworkToolsConfig();
	        	
            this.network_tools_config.fetch({
                url: splunkd_utils.fullpath('/services/admin/network_tools/default'),
                success: function (model, response, options) {
                    console.info("Successfully retrieved the network_tools configuration");

                    // Set the index setting
                    mvc.Components.getInstance("index").val(model.entry.associated.content.attributes.index);

                }.bind(this),
                error: function () {
                    console.warn("Unable to retrieve the network_tools configuration");
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
            this.network_tools_config.entry.content.set({
                index: mvc.Components.getInstance("index").val()
            }, {
                silent: true
            });

            // Kick off the request to edit the entry
            var saveResponse = this.network_tools_config.save();

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

                    // Set the app as configured so that users are not forced to re-run setup.
                    this.setConfigured();

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

        render: function () {

            // Start the process of the getting the network_tools.conf settings
            this.getNetworkToolsConfig();

            // Determine if the user has the capability to do the setup
        	var has_permission = this.userHasAdminAllObjects();
        	
            // Render the HTML
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