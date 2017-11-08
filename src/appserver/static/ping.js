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

            	default_search: '| search sourcetype=ping $index$ | head 1 | table dest sent received packet_loss min_ping avg_ping max_ping jitter',
            	fresh_search: '| ping $host$ $count$ $index$',
            	search_token: 'ping_search',

				token_name : 'host',
				token_input_id: 'host_input'
			});

			network_tools_view.getSearchParams = function(){
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
					return;
				}

				return params;
			};
});
