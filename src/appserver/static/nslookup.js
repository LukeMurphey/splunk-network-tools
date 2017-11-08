require.config({
    paths: {
    	network_tools_view: '../app/network_tools/js/views/NetworkToolsView'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'splunkjs/mvc/tokenutils', 'network_tools_view', 'bootstrap.tab', 'splunkjs/mvc/simplexml/ready!'],
		function($, _, mvc, TokenUtils, NetworkToolsView){

			var network_tools_view = new NetworkToolsView({
				execute_button_id : "#execute_input",
				cell_renderer_id : 'element2',

            	default_search: '| search sourcetype=nslookup $index$ | head 1 | fields - _raw _time | fields query a aaaa mx ns',
            	fresh_search: '| nslookup $host$ $index$',
            	search_token: 'nslookup_search',

				token_name : 'host',
				token_input_id: 'host_input'
			});
	
});