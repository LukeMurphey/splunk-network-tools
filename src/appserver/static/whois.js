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

            	default_search: '| search sourcetype=whois | head 1 | fields * | fields - _* date_* host source sourcetype time index linecount splunk_server raw tag eventtype tag::eventtype | eval row="value" | transpose column_name=attribute header_field=row | regex value=".+"',
            	fresh_search: '| whois $host$',
            	search_token: 'whois_search',

				token_name : 'host',
				token_input_id: 'host_input'
			});
});

