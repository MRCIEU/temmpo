// Add function to record change via jsTree
$('#term_tree').on("changed.jstree", function (e, data) {

    // on change - merge selected tree nodes with subset of previously selected nodes that do not exist in the tree 

    var previously_selected_nodes = $('#term_tree_ids').val().split(","); ;
    var unloaded_selected_nodes = [];

    for (i = 0; i < previously_selected_nodes.length; i++) {
    	node = previously_selected_nodes[i];

    	obj_tree = data.instance.get_node(node); //$('#term_tree').get_node(node);
    	console.log("node");
		console.log(node);
    	console.log("obj_tree");
    	console.log(obj_tree);
    	if (!obj_tree){
    		unloaded_selected_nodes.push(node);
    		console.log("attempt push node");
    	}
	}

	unloaded_selected_nodes_str = unloaded_selected_nodes.join()

	if (unloaded_selected_nodes_str &&  data.selected){
		$('#term_tree_ids').val(data.selected + "," + unloaded_selected_nodes_str);
	} else {
    	$('#term_tree_ids').val(data.selected);
	}	
});
