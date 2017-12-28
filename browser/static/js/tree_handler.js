// Add function to record changes made via jsTree
$('#term_tree').on("changed.jstree", function (e, data) {

    // on change - merge selected tree nodes with subset of previously selected nodes that do not exist in the tree

    // console.log("Before change hidden ids")
    // console.log($('#term_tree_ids').val())
    // console.log("data.selected");
    // console.log(data.selected);
    // console.log("data.deselected");
    // console.log(data.deselected);
    var previously_selected_nodes = $('#term_tree_ids').val().split(","); ;
    var unloaded_selected_nodes = [];

    // console.log("e")
    // console.log(e)
    // console.log("#term_tree_ids")
    // console.log($('#term_tree_ids').val())
    // console.log("previously_selected_nodes");
    // console.log(previously_selected_nodes);

    for (i = 0; i < previously_selected_nodes.length; i++) {
        node = previously_selected_nodes[i];
    	obj_tree = data.instance.get_node(node); //$('#term_tree').get_node(node);
  //   	console.log("node");
		// console.log(node);
  //   	console.log("obj_tree");
  //   	console.log(obj_tree);
    	if (!obj_tree){
    		unloaded_selected_nodes.push(node);
        // console.log("Attempt push node");
    	}
	}

	unloaded_selected_nodes_str = unloaded_selected_nodes.join()

    // console.log("unloaded_selected_nodes_str")
    // console.log(unloaded_selected_nodes_str)
    // console.log("data.selected")
    // console.log(data.selected)

	if (unloaded_selected_nodes_str && data.selected){
        // console.log("There are hidden previously selected nodes - updating hidden field with unloaded and visisble selected tree node ids")
		$('#term_tree_ids').val(data.selected + "," + unloaded_selected_nodes_str);
	} else {
        // console.log("No hidden selected nodes - updating hidden field with currently selected and visible tree node ids")
    	$('#term_tree_ids').val(data.selected);
	}

    // console.log("After change selected tree ids:")
    // console.log($('#term_tree_ids').val())

});
