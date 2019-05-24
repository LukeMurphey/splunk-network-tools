require.config({
    paths: {
    	network_tools_view: '../app/network_tools/js/views/NetworkToolsView'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'splunkjs/mvc/tokenutils', 'network_tools_view', 'bootstrap.tab', 'splunkjs/mvc/simplexml/ready!'],
		function($, _, mvc, TokenUtils
			, NetworkToolsView){

			var network_tools_view = new NetworkToolsView({
				cell_renderer_id : 'element4',
				execute_button_id : "#execute_input",

            	default_search: '| search sourcetype=portscan $index$ | head 1 | table dest port status',
            	fresh_search: '| portscan $dest$ $ports$ $index$',
            	search_token: 'portscan_search',

				token_name : 'dest',
				token_input_id: 'dest_input'
			});

			network_tools_view.getSearchParams = function(){
				var params = {
					'dest' : '',
					'ports' : '',
				};
				
				// Get the server to use (if provided)
				var dest_input = mvc.Components.getInstance("dest_input");
				
				if(dest_input && dest_input.val() && dest_input.val().length > 0){
					params['dest'] = 'dest=' + dest_input.val();
				}
				else{
					alert("Please enter the name of a host to perform the port scan");
					return;
				}

				// Get the ports to use
				var port_input = mvc.Components.getInstance("ports_input");
				
				if(port_input && port_input.val() && port_input.val().length > 0){
					params['ports'] = 'ports="' + port_input.val() + '"';
				}

				return params;
			};
});
