require.config({
    paths: {
    	network_tools_cell_renderer: '../app/network_tools/NetworkToolsCellRenderer'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'splunkjs/mvc/tokenutils', 'network_tools_cell_renderer', 'bootstrap.tab', 'splunkjs/mvc/simplexml/ready!'],
		function($, _, mvc, TokenUtils, NetworkToolsCellRenderer){
	
	// Setup the cell renderer
    var resultsTable = mvc.Components.get('element4');
    
    resultsTable.getVisualization(function(tableView){
        tableView.table.addCellRenderer(new NetworkToolsCellRenderer());
        tableView.table.render();
    });
	
	// Run the test
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
		tokens.set('traceroute_search', null);
		tokens.set('traceroute_search', TokenUtils.replaceTokenNames('| traceroute $host$', params ));
	};

	// Handle a click event from the execute button and force the search command to execute.
	$("#execute_input").click(run_test);
	
	// By default, show the most recent traceroute result. To do this, we will set the traceroute search token to be a historical search.
	var tokens = mvc.Components.getInstance("submitted");
	tokens.set('traceroute_search', '| search sourcetype=traceroute | head 1 | join unique_id max=300 [| search sourcetype=traceroute | eval raw=_raw] | rex field=raw "rtt=\\"(?<rtt>[.0-9]+)\\"" max_match=5 | rex field=raw "name=\\"(?<name>[.0-9]+)\\"" max_match=5 | rex field=raw "ip=\\"(?<ip>[.0-9]+)\\"" max_match=5 | stats values(rtt) as rtt values(ip) as ip values(name) as name first(dest_host) as dest_host first(dest_ip) as dest_ip by hop | sort hop');
	
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