$(function() {
	listDatasources();
	
	/* actions */
	
	$("#ds-update").live("click", function() {
		updateDatasource();
		// refresh list
	});
	
	/* menu */
	// cmd buttons
	$("#ds-refresh").click(function () {
		$("#workspace").html("");
		listDatasources();
	});
	
	$("#ds-add").click(function () {
		$.get("forms/ds-add.html", function(data) {
			$("#workspace").html(data);
		});
	});
	
	$("#config").click(function () {		
		$.get("forms/config.html", function(data) {
			$("#workspace").html(data);
		});
	});
	
	// select a data source into the workspace
	$(".datasource").live("click", function() {
		var dsID = $(this).attr("resource");
		var dsTitle = $(this).text();
		$.get("forms/ds-work.html", function(data) {
			$("#workspace").html(data);
			$("#ws-selected-ds").html("<a href='" + dsID + "'>" + dsTitle + "</a>");
		});
		// default tab is 'Query'
		selectTab("ws-tab-query", dsID);
	});

	// tab selection
	$(".ws-tab").live("click", function() {
		var tabID = $(this).attr("id");
		var dsID = $("#ws-selected-ds a").attr("href");
		
		$(".ws-tab").each(function() {
			$(this).removeClass("active-tab");
		});
		$(this).addClass("active-tab");
		selectTab(tabID, dsID);
	});
	
	// sync
	$("#ds-sync").live("click", function () {
		var dsID = $("#ws-selected-ds a").attr("href");
		$.get(dsID + '/sync', function(data) {
			selectTab('ws-tab-status', dsID);
		});
	});
	
	
	// hoover effects
	$(".datasource").live("mouseover", function() {
		$(this).css("color", "#44A");
	}).live("mouseout", function() {
		$(this).css("color", "#000");
	});
	
	$(".cmdbtn").mouseover(function () {
		$(this).css("border", "1px solid #c0c0e0");
	}).mouseout(function(){
		$(this).css("border", "1px solid #f0f0f0");
	});
});


function listDatasources(){
	$.getJSON("../api/datasource/all", function(data) {
		var b = "";
		for(i in data) {
			var ds = data[i];
			b += "<div class='datasource' resource='" + ds["id"] + "'><img src='img/ds.png' alt='Data source ...' title='Data source ...' /> " + ds["name"] + "</div>";
		}
		$("#datasources").html(b);
	});
}

function updateDatasource(){
	var dsid = $("#ds-id").text()
	var dsdata = {
		name : $("#ds-name").val(),
		access_method : $("#ds-access").val(),
		access_uri : $("#ds-access-uri").val(),
		access_mode : $("input:radio[name='ds-mode']:checked").val()
	};
	
	dsdata = $.toJSON(dsdata);

	var noun = "../api/datasource";
	
	if(dsid != '') {
		noun = dsid + "/";
	}
	
	$.ajax({
		type: "POST",
		url: noun,
		data: "dsdata="+ dsdata,
		success: function(data){
			listDatasources();
		},
		error:  function(msg){
			alert(msg);
		} 
	});
}

function selectTab(tabID, dsID) {
	var tabMap = { 
		"ws-tab-query" : "forms/ds-query.html",
		"ws-tab-schema" : "forms/ds-schema.html",
		"ws-tab-export" : "forms/ds-export.html"
	}

	if(tabID == "ws-tab-admin") {
		$.get("forms/ds-add.html", function(data) {
			$("#ws-main").html(data);
			// adapt form
			$("#ws-main .pane-title").html("");
			$("#ws-main #ds-update").text("Update");
		});
		// set form values
		$.getJSON(dsID, function(data) {
			$("#ds-id").text(data.id);
			$("#ds-name").val(data.name);
			$("#ds-access option[value='" + data.access_method + "']").attr("selected", true);
 			$("#ds-access-uri").val(data.access_uri);
			$("input:radio[name='ds-mode'][value='" + data.access_mode +"']").attr('checked', true);
		});
		return;
	}

	if(tabID == "ws-tab-status") {
		$.get("forms/ds-status.html", function(data) {
			$("#ws-main").html(data);
		});
		// set form values
		$.getJSON(dsID, function(data) {
			$("#ds-last-update").text(data.updated);
			if(data.access_mode == 'local') {
				$("#ds-last-sync").text(data.last_sync);
			}
			else {
				$("#ds-last-sync").text('N/A');
			}
		});
		return;
	}
	
	$.get(tabMap[tabID], function(data) {
		$("#ws-main").html(data);
	});
}

