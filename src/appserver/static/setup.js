
require.config({
    paths: {
        network_tools_setup: "../app/network_tools/js/views/NetworkToolsSetupView"
    }
});

require([
         "jquery",
         "underscore",
         "backbone",
         "network_tools_setup",
         "splunkjs/mvc/simplexml/ready!"
     ], function(
         $,
         _,
         Backbone,
         NetworkToolsSetupView
     )
     {
         
         var networkToolsSetupView = new NetworkToolsSetupView({
        	 el: $('#setupView')
         });
         
         networkToolsSetupView.render();
     }
);
