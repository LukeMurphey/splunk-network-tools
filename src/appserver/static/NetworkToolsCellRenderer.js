define(['jquery', 'underscore', 'splunkjs/mvc', 'views/shared/results_table/renderers/BaseCellRenderer'], function($, _, mvc, BaseCellRenderer) {
    
    var WebsiteStatusCellRenderer = BaseCellRenderer.extend({
    	 canRender: function(cell) {
    		 return ($.inArray(cell.field, ["avg_ping", "max_ping", "min_ping", "packet_loss", "hops"]) >= 0);
    		 //["avg_ping", "max_ping", "min_ping", "jitter", "packet_loss", "hops"]
		 },
		 
		 render: function($td, cell) {
			 
			 // Add the class so that the CSS can style the content
			 $td.addClass(cell.field);
			 
			 var icon = null;
			 
			 // Handle the packet_loss field
			 if( cell.field == "packet_loss" ){
				 
				 var int_value = parseFloat(cell.value, 10);
				 
				 if( int_value == 0 ){
					 $td.addClass("success");
					 icon = 'check';
				 }
				 else if( int_value <= 10 ){
					 $td.addClass("warning");
					 icon = 'alert';
				 }
				 else{
					 $td.addClass("failure");
					 icon = 'alert';
				 }
				
			 }
			 
			 // Handle the hops field
			 if( cell.field == "hops" ){
				 
				 var int_value = parseFloat(cell.value, 10);
				 
				 if( int_value > 30 ){
					 $td.addClass("failure");
					 icon = 'alert';
				 }
				 else if( int_value >= 15 ){
					 $td.addClass("warning");
					 icon = 'alert';
				 }
				 else{
					 $td.addClass("success");
					 icon = 'check';
				 }
				
			 }
			 
			 // Render the cell
			 if( icon != null ){
				 $td.html(_.template('<i class="icon-<%- icon %>"> </i><%- value %>', {
		            	value: cell.value,
		                icon: icon
		         }));
			 }
			 else{
				 $td.html( cell.value );
			 }
		 }
	});
    
    return WebsiteStatusCellRenderer;
});