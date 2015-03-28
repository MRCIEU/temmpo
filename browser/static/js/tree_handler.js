// Set up JStree
// Initialise the JSTree instance
//$(function () { $('#term_tree').jstree(); });
console.log('INIT');
// Add function to record change
$('#term_tree').on("changed.jstree", function (e, data) {
    console.log(data.selected);
    $('#term_data').val(data.selected);
});
