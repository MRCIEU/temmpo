// Add function to record change via jsTree
$('#term_tree').on("changed.jstree", function (e, data) {

    // TODO: BUG: currently overwrites any selected noted that have not been loaded yet, appears you cannot record seleted for items that have not been loaded yet.

    // IDEA: Load all selected and ancestor nodes on first creation of tree, NB: This would reduce performanace - update views.py

    // NB: state plugin seemed to have the same problem

    // IDEA: For nodes that tree does not have loaded in term_data - preserve and merge with currently selected - update js

    // on change - merge selected tree nodes with subset of previously nodes that do not exist in the tree - possible check if undetermined nodes is an ancestor ?? possible can compare using tree_number string comparison
    // TODO: Nodes that have children when selected should also select all child nodes - action in views form handler
    $('#term_data').val(data.selected);
});
