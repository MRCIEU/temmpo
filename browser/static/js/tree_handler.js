// Add function to record change via jsTree
// TODO : Only parent node is being selected
$('#term_tree').on("changed.jstree", function (e, data) {
    // If the item changing is a previously saved item and no longer selected remove from term_data

    // else If changing a new item merge data.selected with current term_data
    $('#term_data').val(data.selected);
    // TODO: BUG: currently overwrites any selected noted that have not been loaded yet
});
