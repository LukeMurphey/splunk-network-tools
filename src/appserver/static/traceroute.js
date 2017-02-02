require(['jquery','underscore','splunkjs/mvc', 'splunkjs/mvc/tokenutils', 'bootstrap.tab', 'splunkjs/mvc/simplexml/ready!'],
		function($, _, mvc, TokenUtils){
	
	// Handle a click event from the execute button and force the search command to execute.
	$( "#execute_input" ).click(function() {
		
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
	});
	
	// By default, show the most recent traceroute result. To do this, we will set the traceroute search token to be a historical search.
	var tokens = mvc.Components.getInstance("submitted");
	tokens.set('traceroute_search', '| search sourcetype=traceroute | head 1 | join unique_id max=100 [| search sourcetype=traceroute] | rex field=_raw "rtt=\\"(?<rtt>[.0-9]+)\\"" max_match=5 | rex field=_raw "name=\\"(?<name>[.0-9]+)\\"" max_match=5 | rex field=_raw "ip=\\"(?<ip>[.0-9]+)\\"" max_match=5 | stats values(rtt) as rtt values(ip) as ip values(name) as name first(dest_host) as dest_host first(dest_ip) as dest_ip by hop');
	
});