require.config({
    paths: {
    	network_tools_view: '../app/network_tools/js/views/NetworkToolsView'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'splunkjs/mvc/tokenutils', 'network_tools_view', 'bootstrap.tab', 'splunkjs/mvc/simplexml/ready!'],
		function($, _, mvc, TokenUtils, NetworkToolsView){

			var network_tools_view = new NetworkToolsView({
				execute_button_id : "#execute_speedtest_input",

            	default_search: '| search sourcetype=speedtest | head 1 | table ping upload download upload_readable download_readable',
            	fresh_search: '| speedtest $runs$ $server$',
            	search_token: 'speedtest_search'
			});

			network_tools_view.getSearchParams = function(){
				// This will contain the parameters
				var params = {
						'runs' : '',
						'server' : ''
				};
				
				// Get the number of runs
				var runs_input = mvc.Components.getInstance("runs_input");
				
				if(runs_input && runs_input.val()){
					params['runs'] = 'runs=' + runs_input.val();
				}
				
				// Get the server to use (if provided)
				var server_input = mvc.Components.getInstance("server_input");
				
				if(server_input && server_input.val()){
					params['server'] = 'server=' + server_input.val();
				}

				return params;
			}
});
