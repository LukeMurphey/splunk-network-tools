/**
 * This view is used to simplify many of the boilerplate operations necessary to run the various Network Toolkit view.
 * 
 * This includes:
 * 
 *   1) Wiring up the cell renderer
 *   2) Wiring up the execute button
 *   3) Running a search to get the last result and replacing it with another search when the user wants to generate a new result
 *   4) Automatically running a test if the URL contains an argument
 */
require.config({
    paths: {
    	network_tools_cell_renderer: '../app/network_tools/NetworkToolsCellRenderer'
    }
});

define([
    'jquery',
    'underscore',
    'splunkjs/mvc',
    'splunkjs/mvc/tokenutils',
    'splunkjs/mvc/simplesplunkview',
    'network_tools_cell_renderer',
    'bootstrap.tab',
    'splunkjs/mvc/simplexml/ready!'
], function(
    $,
    _,
    mvc,
    TokenUtils,
    SimpleSplunkView,
    NetworkToolsCellRenderer
){
	
    // Define the custom view class
    var NetworkToolsView = SimpleSplunkView.extend({
        className: "NetworkToolsView",
        
        defaults: {
        	execute_button_id: "#execute_input",
            cell_renderer_id: null,

            default_search: null,
            fresh_search: null,
            search_token: null,

            // The name of the token to set from the input
            token_name: null,
            token_input_id: null

        },
        
        /**
         * Initialize the class.
         */
        initialize: function() {
        	this.options = _.extend({}, this.defaults, this.options);
        	
            // Handle a click event from the execute button and force the search command to execute.
            $(this.options.execute_button_id).click(this.runTest.bind(this));

            // By default, show the most recent nslookup result. To do this, we will set the nslookup search token to be a historical search.
            var tokens = mvc.Components.getInstance("submitted");
            tokens.set(this.options.search_token, this.options.default_search);

            // Start the test if the URLs parameters call for it.
            this.startTestIfNecessary();

            this.renderCellRenderer();
        },

        /**
         * Render the ell renderer
         */
        renderCellRenderer: function(){

            if(this.options.cell_renderer_id !== null){
                // Setup the cell renderer
                var resultsTable = mvc.Components.get(this.options.cell_renderer_id);
                
                resultsTable.getVisualization(function(tableView){
                    tableView.table.addCellRenderer(new NetworkToolsCellRenderer());
                    tableView.table.render();
                });
            }
        },
	
        /**
         * Get the parameters to run the search.
         */
        getSearchParams: function(){

            // This will contain the parameters
            var params = {};

            params[this.options.token_name] = '';
            
            // Get the host to use
            var host_input = mvc.Components.getInstance(this.options.token_input_id);
            
            if(host_input && host_input.val()){
                params[this.options.token_name] = host_input.val();
            }

            return params;

        },

	    /**
         * Run the test
         */
	    runTest: function() {
            
            // This will contain the parameters
            var params = this.getSearchParams();

            if(params === null){
                return;
            }
            
            // Kick off the search
            var tokens = mvc.Components.getInstance("submitted");
            tokens.set(this.options.search_token, null);
            tokens.set(this.options.search_token, TokenUtils.replaceTokenNames(this.options.fresh_search, params));
        },

	    /**
         * Start the test if the URL parameters call for it
         */
	    startTestIfNecessary: function(){
        
            // See if a host parameter was provided and run the search if necessary
            if(Splunk.util.getParameter(this.options.token_name) !== null){

                // Show the results tab
                $('.results-tab').trigger('click').trigger('shown');

                // Set the host
                var server_input = mvc.Components.getInstance(this.options.token_input_id);
                server_input.val(Splunk.util.getParameter(this.options.token_name));

                // Start the test
                this.runTest();
            }
	    }
        
    });
	
    return NetworkToolsView;
});