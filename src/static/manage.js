$(document).ready(function(){
	$('#all_sites').change(function(){
		var is_checked = $('#all_sites').prop('checked');
		$('input[name="site"]').prop('checked', is_checked)		
	})
})

function perform_ops() {
	var op_name = "";
	var selected = $('input[name="operation"]:checked');
    $('#ajax-msgs').removeClass('hidden').empty().append('<h2>Messages</h2><ul id="msg-list"></ul>');
	if (selected.length > 0) {
	    var site_names = $('input[name="site"]:checked').map(function(){return this.value;});
	    op_name = selected.val();
	    var verbose_opt = $('input[name="verbose"]')[0].checked;
	    var dry_run_opt = $('input[name="dry-run"]')[0].checked;
	    var ajax_tracker = {remaining_ops: site_names.length};
	    if (site_names.length > 0) {
		    $('#msg-list').append('<li id="op-status">Running...</li>')
		    for(var s = 0; s < site_names.length; s++) {
		    	perform_op(site_names[s], op_name, verbose_opt, dry_run_opt, ajax_tracker);
		    }
	    } else {
	    	$('#msg-list').append('<li id="op-status">You didn\'t select any sites</li>')
	    }
	} else {
	    $('#msg-list').append('<li id="op-status">You didn\'t select an operation</li>')
	}	
}

function perform_op(site_name, op_name, verbose_opt, dry_run_opt, ajax_tracker) {
	$.getJSON($SCRIPT_ROOT + '/site-op', {site: site_name,
		op: op_name, verbose: verbose_opt, dry_run: dry_run_opt},
		function(data){
			var msgs = data['msgs'];
			for(i = 0; i < msgs.length; i++) {
				$('#op-status').before('<li>'+msgs[i]+'</li>');
			}
		}).always(function(){
			ajax_tracker.remaining_ops--;
			var status_text = "Still running...";
			if(ajax_tracker.remaining_ops == 0) {
				status_text = "Done!";
			}
			$('#op-status').text(status_text);				
		});
	return false;
}