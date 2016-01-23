$(document).ready(function(){
	$('#all_sites').change(function(){
		var is_checked = $('#all_sites').prop('checked');
		$('input[name="site"]').prop('checked', is_checked)		
	})
})

function perform_ops() {
	var op_name = "";
	var selected = $('input[name="operation"]:checked');
	if (selected.length > 0) {
	    op_name = selected.val();
	    var verbose_opt = $('input[name="verbose"]')[0].checked;
	    var dry_run_opt = $('input[name="dry-run"]')[0].checked;
	    $('#ajax-msgs').empty().append('<h2>Messages</h2><ul id="msg-list"></ul>');
	    $('#msg-list').append('<li id="op-status">Running...</li>')
	    var site_names = $('input[name="site"]:checked').map(function(){return this.value;});
	    for(var s = 0; s < site_names.length; s++) {
	    	var is_last = s == site_names.length - 1
	    	perform_op(is_last, site_names[s], op_name, verbose_opt, dry_run_opt);
	    }
	} else {
		//TODO: Error -- operation not selected
	}	
}

function perform_op(is_last, site_name, op_name, verbose_opt, dry_run_opt) {
	$.getJSON($SCRIPT_ROOT + '/site-op', {site: site_name,
		op: op_name, verbose: verbose_opt, dry_run: dry_run_opt},
		function(data){
			var msgs = data['msgs'];
			for(i = 0; i < msgs.length; i++) {
				$('#op-status').before('<li>'+msgs[i]+'</li>');
			}
			if(is_last) {
				$('#op-status').text("Done!");
			}
		});
	return false;
}