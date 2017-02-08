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
	
	// Handle a click event from the execute button and force the search command to execute.
	$( "#execute_input" ).click(function() {
		
		// This will contain the parameters
		var params = {
				'count' : '',
				'host' : ''
		};
		
		// Get the number of runs
		var runs_input = mvc.Components.getInstance("runs_input");
		
		if(runs_input && runs_input.val()){
			params['count'] = 'count=' + runs_input.val();
		}
		
		// Get the server to use (if provided)
		var server_input = mvc.Components.getInstance("server_input");
		
		if(server_input && server_input.val() && server_input.val().length > 0){
			params['host'] = 'host=' + server_input.val();
		}
		else{
			alert("Please enter the name of a host to perform the ping against");
			return false;
		}
		
		
		// Kick off the search
		var tokens = mvc.Components.getInstance("submitted");
		tokens.set('ping_search', null);
		tokens.set('ping_search', TokenUtils.replaceTokenNames('| ping $host$ $count$', params ));
	});
	
	// By default, show the most recent speedtest result. To do this, we will set the speedtest search token to be a historical search.
	var tokens = mvc.Components.getInstance("submitted");
	tokens.set('ping_search', '| search sourcetype=ping | head 1 | table dest sent received packet_loss min_ping avg_ping max_ping jitter');
	
});