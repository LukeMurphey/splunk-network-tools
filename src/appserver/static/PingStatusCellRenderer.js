define(['jquery', 'underscore', 'splunkjs/mvc', 'views/shared/results_table/renderers/BaseCellRenderer'], function($, _, mvc, BaseCellRenderer) {
    
    var PingStatusCellRenderer = BaseCellRenderer.extend({
    	 canRender: function(cell) {
    		 return ($.inArray(cell.field, ["dest", "ping", "max_ping", "packet_loss", "average"]) >= 0);
		 },
		 
		 render: function($td, cell) {
			 
			 // Add the class so that the CSS can style the content
			 $td.addClass(cell.field);
			 
			 var icon = null;
			 
			 // Handle the ping value
			 if(cell.field == "ping" || cell.field == "max_ping"){
                
                var float_value = parseFloat(cell.value, 10);
                
                if( float_value >= 1000 ){
                    $td.addClass("failure");
                    icon = 'alert';
                }
                else{
                    $td.addClass("success");
                    
                    var percent = 0;
                    
                    if(float_value <= 100){
                        percent = 0;
                    }else if(float_value <= 250){
                        percent = 25;
                    }
                    else if(float_value <= 500){
                        percent = 50;
                    }
                    else if(float_value <= 750){
                        percent = 75;
                    }
                    else if(float_value <= 1000){
                        percent = 100;
                    }
                    else{
                        percent = null;
                    }
                    
                    if(percent !== null){
                        $td.html(_.template('<i class="stopwatch-icon-<%- percent %>" /> <%- value %>', {
                               value: cell.value,
                               percent: percent
                        }));
                        
                        $td.addClass("response-" + percent);
                        
                        return;
                    }
                }   
            }

			 
			 // Handle the ping value
			 else if(cell.field == "packet_loss"){

                // Assign the classes based on the ping time
                var loss_value = parseInt(cell.value, 10);
                
                if(loss_value == 0){
                    $td.addClass("success");
                    icon = 'check';
                    cell.value = loss_value + " %";
                }
                else if(loss_value <= 10){
                    $td.addClass("warning");
                    icon = 'alert';
                    cell.value = loss_value + " %";
                }
                else{
                    $td.addClass("failure");
                    icon = 'alert';
                    if(!isNaN(loss_value)){
                        cell.value = loss_value + " %";
                    }
                }
            }
			 
			 // Render the cell
			 if(icon !== null){
				 $td.html(_.template('<i class="icon-<%- icon %>"> </i><%- value %>', {
		            	value: cell.value,
		                icon: icon
		         }));
			 }
			 else{
				 $td.html(cell.value);
			 }
		 }
	});
    
    return PingStatusCellRenderer;
});