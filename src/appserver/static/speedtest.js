require(['jquery','underscore','splunkjs/mvc', 'splunkjs/mvc/tokenforwarder', 'bootstrap.tab', 'splunkjs/mvc/simplexml/ready!'],
		function($, _, mvc, TokenForwarder){
	
	var speedtest_executed = false;
	
	// Handle a click event from the execute button and force the search command to execute.
	$( "#execute_speedtest_input" ).click(function() {
		speedtest_executed = true;
		
		// This is the search
		var search = '| speedtest';
		
		//
		var runs_input = mvc.Components.getInstance("runs_input");
		
		if(runs_input && runs_input.val()){
			search += ' runs=' + runs_input.val();
		}
		
		var server_input = mvc.Components.getInstance("server_input");
		
		if(server_input && server_input.val()){
			search += ' server=' + server_input.val();
		}
		
		alert(search);
		
		var tokens = mvc.Components.getInstance("submitted");
		//tokens.set('speedtest_search', search);
		  
	});
	
	// By default, show the most recent speedtest result
	var tokens = mvc.Components.getInstance("submitted");
	tokens.set('speedtest_search', '| search sourcetype=speedtest | head 1 | table ping upload download upload_readable download_readable');
	
});