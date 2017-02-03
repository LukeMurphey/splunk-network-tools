
require.config({
    paths: {
        wol_list: "../app/network_tools/js/views/WakeOnLanHostListView"
    }
});

require([
         "jquery",
         "underscore",
         "backbone",
         "wol_list",
         "splunkjs/mvc/simplexml/ready!"
     ], function(
         $,
         _,
         Backbone,
         WakeOnLanHostListView
     )
     {
         
         var wakeOnLanHostListView = new WakeOnLanHostListView({
        	 el: $('#wakeonlan_list')
         });
         
         wakeOnLanHostListView.render();
     }
);