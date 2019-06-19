require.config({
    paths: {
    	ping_status_cell_renderer: '../app/network_tools/PingStatusCellRenderer'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'ping_status_cell_renderer', 'splunkjs/mvc/searchmanager', 'splunkjs/mvc/simplexml/ready!'],
	function($, _, mvc, PingStatusCellRenderer, SearchManager){
	
		// Setup the cell renderer
	    var statusTable = mvc.Components.get('element6');
	
	    statusTable.getVisualization(function(tableView){
	        tableView.table.addCellRenderer(new PingStatusCellRenderer());
	        tableView.table.render();
	    });   
	}
);