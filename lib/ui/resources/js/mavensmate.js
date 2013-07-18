child_metadata = [ 
  {"xmlName" : "CustomField", "tagName" : "fields", "parentXmlName" : "CustomObject" }, 
  {"xmlName" : "BusinessProcess", "tagName" : "businessProcesses", "parentXmlName" : "CustomObject" }, 
  {"xmlName" : "RecordType", "tagName" : "recordTypes", "parentXmlName" : "CustomObject" }, 
  {"xmlName" : "WebLink", "tagName" : "webLinks", "parentXmlName" : "CustomObject" }, 
  {"xmlName" : "ValidationRule", "tagName" : "validationRules", "parentXmlName" : "CustomObject" }, 
  {"xmlName" : "NamedFilter", "tagName" : "namedFilters", "parentXmlName" : "CustomObject" }, 
  {"xmlName" : "SharingReason", "tagName" : "sharingReasons", "parentXmlName" : "CustomObject" }, 
  {"xmlName" : "ListView", "tagName" : "listViews", "parentXmlName" : "CustomObject" }, 
  {"xmlName" : "FieldSet", "tagName" : "fieldSets", "parentXmlName" : "CustomObject" },
  {"xmlName" : "CustomLabel", "tagName" : "customLabels", "parentXmlName" : "CustomLabels" },
  {"xmlName" : "WorkflowAlert", "tagName" : "alerts", "parentXmlName" : "Workflow" },
  {"xmlName" : "WorkflowTask", "tagName" : "tasks", "parentXmlName" : "Workflow" },
  {"xmlName" : "WorkflowOutboundMessage", "tagName" : "outboundMessages", "parentXmlName" : "Workflow" },
  {"xmlName" : "WorkflowFieldUpdate", "tagName" : "fieldUpdates", "parentXmlName" : "Workflow" },
  {"xmlName" : "WorkflowRule", "tagName" : "rules", "parentXmlName" : "WorkFlow", "parentXmlName" : "Workflow" }, 
  {"xmlName" : "WorkflowEmailRecipient", "tagName" : "emailRecipients", "parentXmlName" : "Workflow" },
  {"xmlName" : "WorkflowTimeTrigger", "tagName" : "timeTriggers", "parentXmlName" : "Workflow" },
  {"xmlName" : "WorkflowActionReference", "tagName" : "actionReferences", "parentXmlName" : "Workflow" }
]

$(function() {
	
});

function scrollToTop(selector) {
	$(selector).animate({ scrollTop: 0 }, 300);
}

function showElement(id) {
	$("#"+id).show();
}

function hideElement(id) {
	$("#"+id).hide();
}

function toggleRunningIndicator() {
	$(".running_indicator").toggle();
}

function showLoading(message) {
	$(".twipsy").height($(window).height())
	$(".twipsy").width($(window).width())
	$("#loading_message").html(message)
	$(".loading").show();
}

function hideLoading() {
	$(".loading").hide();
}

//window resizer and mover
function resizeAndCenterWindow() {
	resizeWindow();
	centerWindow();
} 

function isArray(what) {
    return Object.prototype.toString.call(what) === '[object Array]';
}

//window resizer and mover
function resizeAndCenterWindowByHeight(height) {
   	window.resizeTo(485, height+160);
	try {
		$("#deploy_output").height(height);
	} catch(e) { }	
	//window.moveTo((screen.width-385)/2,(screen.height-document.getElementById('wrapper').offsetHeight-400)/2);
}

//window resizer and mover
function resizeAndCenterWindowSpecific(width, height) {
   	window.resizeTo(width, height+160);
	try {
		$("#deploy_output").height(height);
	} catch(e) { }	
	window.moveTo((screen.width-width)/2,(screen.height-document.getElementById('wrapper').offsetHeight-(width+15))/2);
}

function resizeWindow() {
   	window.resizeTo(385, document.getElementById('wrapper').offsetHeight+72);
	try {
		$("#deploy_output").height(document.getElementById('wrapper').offsetHeight);
	} catch(e) { } 
}

function centerWindow() {
	window.moveTo((screen.width-$(window).width())/2,(screen.height-$(window).height())/2-190);
}   

//if dom elements is removed, we need to resize the window
function resizeWindowOnDomElementRemoved() {
	$( "body" ).bind(
		"DOMNodeRemoved",
		function( event ) {
			if (event.target.id == "result_wrapper") {
				resizeWindow();
				$("#project_details_tab").click();
			}
		}
	);
}  

//submit form on enter
function submitFormOnEnter() {
	//submit form on enter
	$(".content").bind('keyup', function(e) {
		var code = (e.keyCode ? e.keyCode : e.which);
		 if(code == 13) { //enter pressed
		 	//if ($('#un').val() && $('#pw').val() && $('#pn').val())
				$("#btnSubmit").click();
		 }
	}); 
} 

//gets tree content in ruby hash form
function get_tree() {			
	var json = { }
	var tree = $("#tree").dynatree("getTree")
	var child_def = {}
	for (item in child_metadata) {
		child_def[child_metadata[item]['tagName']] = child_metadata[item]['xmlName']
	}
	try {
		//process top level (these are top level metadata types)
		var selected_items = tree.getSelectedAndPartselNodesByLevel(1)
		for (var i in selected_items) {
			json[selected_items[i].data.title] = selected_items[i].bSelected && !selected_items[i].data.inFolder && !selected_items[i].data.in_folder ? "*" : []
		} 
		
		
		//process children (can either be files or folders)
		selected_items = tree.getSelectedAndPartselNodesByLevel(2)
		for (var i in selected_items) {
			if (json[selected_items[i].parent.data.title] == "*") continue;   
			if (selected_items[i].parent.data.hasChildTypes == true && !selected_items[i].bSelected) continue;
			json[selected_items[i].parent.data.title].push(selected_items[i].data.title)
		}
		
		//console.log('after second level processing')
		//return json
		
		//process grandchildren (this is either metadata in folders or child metadata types like fields, weblinks, listviews, etc.)
		selected_items = tree.getSelectedAndPartselNodesByLevel(3)
		for (var i in selected_items) {
			if (selected_items[i].parent.parent.data.inFolder || selected_items[i].parent.parent.data.in_folder) {
				//this is folder-based metadata, we need to add this item explicitly
			    items = json[selected_items[i].parent.parent.data.title] //=> items is an array
			  	var item;
				folder_name = ""
				for (var j = 0; j < items.length; j++) {
					if (items[j].name == selected_items[i].parent.data.title) {
						folder_name = items[j].name
						item = items[j]
						break;
					}
				} 
				//console.log(item)
				items.push(selected_items[i].parent.data.title + "/" + selected_items[i].data.title)
			} else if (selected_items[i].parent.parent.data.hasChildTypes) {
				//this is metadata types like weblinks, fields, etc.
				//console.log('processing child item')
				//console.log(selected_items[i])
				if (selected_items[i].parent.parent.data.select || selected_items[i].parent.parent.bSelected) {
					//console.log('topmost parent is selected, continuing')
					continue;
				} else {
					if (selected_items[i].parent.data.select || selected_items[i].parent.bSelected) {
						console.log('direct parent is selected, continuing')
						continue;
					}
					metadata_type = child_def[selected_items[i].data.title]
					//console.log('type is: ')
					//console.log(metadata_type)
					if (!json[metadata_type]) {
						json[metadata_type] = []
					}    
					//console.log(metadata_type)
					for (var j = 0; j < selected_items[i].childList.length; j++) {
						//console.log(selected_items[i].childList[j])
						if (selected_items[i].childList[j].bSelected || selected_items[i].childList[j].data.select) {
							json[metadata_type].push(selected_items[i].parent.data.title+"."+selected_items[i].childList[j].data.title)  
						}
					}
				}
			}
		}      
		for (item in json) {
			if (json[item] !== "*" && json[item].length == 0) {
				delete json[item]
			}
		} 
	} catch(e) {
		return []
	}
	return json
}

function get_log_levels_json() {
	var options = []
	var logCategories = ['Db', 'Workflow', 'Validation', 'Callout', 'Apex_code', 'Apex_profiling']
	for (category in logCategories) {
		var logCategory = logCategories[category]
		var logLevel = $("#select-"+logCategory).val()
		if (logLevel != '') {
			options.push({
				"category" 	: logCategory,
				"level" 	: logLevel
			})
		}
	}
	return options
}

function setUpAjaxErrorHandling() {
	$.ajaxSetup({
        error: function(jqXHR, exception) {
            try {
            	errorMessage = ''
	            if (jqXHR.status === 0) {
	               	errorMessage = 'Not connected.\n Verify Network.'
	            } else if (jqXHR.status == 404) {
	                errorMessage = 'Requested page not found. [404]'
	            } else if (jqXHR.status == 500) {
	                errorMessage = 'Internal Server Error [500].'
	            } else if (exception === 'parsererror') {
	                errorMessage = 'Requested JSON parse failed.'
	            } else if (exception === 'timeout') {
	                errorMessage = 'Timeout error.'
	            } else if (exception === 'abort') {
	                errorMessage = 'Ajax request aborted.'
	            } else {
	                errorMessage = 'Uncaught Error.\n' + jqXHR.responseText
	            }
	            $("#error_message").html(errorMessage)
    			hideLoading()
            } catch(e) {
            	console.log(e)
            }
        },
        timeout: 3600000
    });
}

function resize_games() {
	$(".flash_game").css("width", $(window).width() - 20)
	$(".flash_game").css("height", $(window).height() - 225)
}

var CHECK_STATUS_INTERVAL = 3000

function global_init_handler(data) {
	console.log(data)
	try {
		var response = JSON.parse(data.responseText)
		check_status(response["id"])
	} catch(e) {
		show_global_error('The local MavensMate server did not respond properly. This likely means it is not running or it is malfunctioning. If MavensMate.app is not running, please start it. Otherwise, try restarting MavensMate.app.');
		hideLoading()
	}
}

function show_global_error(message) {
	$("#global_message").html(message)
	$("#global_message_wrapper").show()
}

function hide_global_error() {
	$("#global_message_wrapper").hide()
	$("#global_message").html('')
}

function show_message(message, mtype) {
	if (mtype === undefined) {
		mtype = 'error'
	}
	$("#error_message").parent().attr('class', 'alert')
	$("#error_message").parent().addClass('alert-'+mtype)
	$("#error_message").html(message)
	$("#result_output").show()
	resizeElements()
}

function hide_message(message) {
	$("#error_message").html('')
	$("#result_output").hide()
	resizeElements()
}

function resize_arcade() {
	$(".flash_game").css("width", $(".tab-content").width() - 45)
	$(".flash_game").css("height", $(window).height() - 270)
}

function resizeElements() {
    // if ($("#result_output").css('display') != 'none') {
    //     if ($(".tab-content").hasClass('tab-content-nested')) {

    //     } else {
    //     	$(".tab-content").height($(window).height() - $(".navbar").height() - $("#result_output").height() - 140)
    //     }
    // } else {
    //     if ($(".tab-content").hasClass('tab-content-nested')) {

    //     } else {
    //     	$(".tab-content").height($(window).height() - $(".navbar").height() - 120)
    //     }
    // }

    if ($("#result_output").css('display') != 'none') {
		$("#main-tab-content").height($(window).height() - $(".navbar").height() - $("#result_output").height() - 140)
    } else {
        $("#main-tab-content").height($(window).height() - $(".navbar").height() - 120)
    }
}

function resizeProjectWrapper(offset) {
	if (offset === undefined) {
		offset = 90
	}
	$("#project_wrapper").height($("#main-tab-content").height() - offset)
}

function check_status(request_id) {
	$.ajax({
		type: "GET",
		url: "http://127.0.0.1:9000/status", 
		data: {
			 id: request_id
		},
		complete: function(data, status, xhr) {
			try {
				console.log('checking status of async request')
			    console.log(data)
			    console.log('json response: ')
			    console.log(data.responseText)
			    var response = JSON.parse(data.responseText)
				if (response["status"] == 'pending') {
			    	setTimeout(function() { check_status(request_id); }, CHECK_STATUS_INTERVAL); //poll for completed async request
			    } else {
			    	handle_response(response);
			    }
			} catch(e) {
				console.log(e)
				console.log('caught an error, polling again...')
				setTimeout(function() { check_status(request_id); }, 2000);
			}
						
		} 
	});
}


jQuery.fn.selectText = function(){
	var doc = document;
	var element = this[0];
	console.log(this, element);
	if (doc.body.createTextRange) {
		var range = document.body.createTextRange();
		range.moveToElementText(element);
		range.select();
	} else if (window.getSelection) {
		var selection = window.getSelection();        
		var range = document.createRange();
		range.selectNodeContents(element);
		selection.removeAllRanges();
		selection.addRange(range);
	}
};

function filter_tree(searchTerm, parent) {
	if (searchTerm === undefined || searchTerm.length < 2) {
		return;
	}
	if (parent === undefined) {
		parent = 'ApexClass'
	}
	var st = searchTerm.toLowerCase()
	$("#tree").dynatree("getRoot").visit(function(node) {
		if (node.data.level == 1) {
			if (node.data.title == parent) {
				node.expand(true);
				node.visit(function(child_node) {
					
					var nodeTitle = child_node.data.title;
					var nt = nodeTitle.toLowerCase()
					if ( nt.indexOf(st) >= 0 ) {
						$(child_node.li).show();
						child_node.visitParents(function(parent_node) {
							$(parent_node.li).show();
							return (parent_node.parent != null);
						}, false); 
						return 'skip';  
					} else {
						$(child_node.li).hide();
					}

				}, false);
			} else {
				$(node.li).hide();
			}
		}
	});
}

function expandAll() {
	$("#tree").dynatree("getRoot").visit(function(node){
		if (node.hasChildren()) {
			node.expand(true);
		}
	});
}

function collapseAll() {
	$("#tree").dynatree("getRoot").visit(function(node){
		node.expand(false);
	});
}

var isTreeFiltered = false;

function submitSearch() {
	var filter = $("#txtFilter").val();
	if (filter && filter.length > 2) {
		tree.filterByText(filter);
		//filter_tree(filter, $('#meta_type').val());
		//scrollToTop("#project_wrapper");
		$("#search-btn").removeClass('btn-success').addClass('btn-danger').html('<i class="icon-remove"></i>')
	}
}

function clearFilter() {
	tree.clearFilter();
	$('#txtFilter').val('');
	$('#txtFilter').focus();
	$("#search-btn").removeClass('btn-danger').addClass('btn-success').html('<i class="icon-search"></i>');
	tree.collapseAll();
}

$.expr[':'].Contains = function(a, i, m) {
	return (a.textContent || a.innerText || "").toUpperCase().indexOf(m[3].toUpperCase()) >= 0;
};