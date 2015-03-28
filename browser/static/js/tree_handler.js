// Add function to record change via jsTree
$('#term_tree').on("changed.jstree", function (e, data) {
    $('#term_data').val(data.selected);
});
