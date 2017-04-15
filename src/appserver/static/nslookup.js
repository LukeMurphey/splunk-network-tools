require.config({
    paths: {
    	network_tools_cell_renderer: '../app/network_tools/NetworkToolsCellRenderer'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'splunkjs/mvc/tokenutils', 'network_tools_cell_renderer', 'bootstrap.tab', 'splunkjs/mvc/simplexml/ready!'],
		function($, _, mvc, TokenUtils, NetworkToolsCellRenderer){
	
	// Setup the cell renderer
    var resultsTable = mvc.Components.get('element2');
    
    resultsTable.getVisualization(function(tableView){
        tableView.table.addCellRenderer(new NetworkToolsCellRenderer());
        tableView.table.render();
    });
	
	// Here is a function to run the test
	var run_test = function() {
		
		// This will contain the parameters
		var params = {
				'host' : ''
		};
		
		// Get the host to use
		var host_input = mvc.Components.getInstance("host_input");
		
		if(host_input && host_input.val()){
			params['host'] = host_input.val();
		}
		
		// Kick off the search
		var tokens = mvc.Components.getInstance("submitted");
		tokens.set('nslookup_search', null);
		tokens.set('nslookup_search', TokenUtils.replaceTokenNames('| nslookup $host$', params ));
	};
	
	// Handle a click event from the execute button and force the search command to execute.
	$("#execute_input").click(run_test);

	// By default, show the most recent nslookup result. To do this, we will set the nslookup search token to be a historical search.
	var tokens = mvc.Components.getInstance("submitted");
	tokens.set('nslookup_search', '| search sourcetype=nslookup | head 1 | fields - _raw _time | fields query a aaaa mx ns');

	// This function will start the test if the URL parameters call for it
	var start_test_if_necessary = function(){
	
		// See if a host parameter was provided and run the search if necessary
		if(Splunk.util.getParameter("host") !== null){

			// Show the results tab
			$('.results-tab').trigger('click').trigger('shown');

			// Set the host
			var server_input = mvc.Components.getInstance("host_input");
			server_input.val(Splunk.util.getParameter("host"));

			// Start the test
			run_test();
		}
	};

	start_test_if_necessary();
	
});