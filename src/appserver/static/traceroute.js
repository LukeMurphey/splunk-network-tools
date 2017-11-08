require.config({
    paths: {
    	network_tools_view: '../app/network_tools/js/views/NetworkToolsView'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'splunkjs/mvc/tokenutils', 'network_tools_view', 'bootstrap.tab', 'splunkjs/mvc/simplexml/ready!'],
		function($, _, mvc, TokenUtils, NetworkToolsView){

			var network_tools_view = new NetworkToolsView({
				execute_button_id : "#execute_input",
				cell_renderer_id : 'element4',

            	default_search: '| search sourcetype=traceroute $index$ | head 1 | join unique_id max=300 [| search sourcetype=traceroute $index$ | eval raw=_raw] | rex field=raw "rtt=\\"(?<rtt>[.0-9]+)\\"" max_match=5 | rex field=raw "name=\\"(?<name>[.0-9]+)\\"" max_match=5 | rex field=raw "ip=\\"(?<ip>[.0-9]+)\\"" max_match=5 | stats values(rtt) as rtt values(ip) as ip values(name) as name first(dest_host) as dest_host first(dest_ip) as dest_ip by hop | sort hop',
            	fresh_search: '| traceroute $host$ $index$',
            	search_token: 'traceroute_search',

				token_name : 'host',
				token_input_id: 'host_input'
			});
	
});
