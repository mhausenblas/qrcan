$(function() {
	listDatasources();
	
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
	
	/* actions */
	
	// add or update data source
	$("#ds-update").live("click", function() {
		updateDatasource();
		if($("#ds-update").text() == "Add ..."){ // adding new data source
			$("#workspace").html("");
		}
		else { // update existing data source
			var dsID = $("#ws-selected-ds a").attr("href");
			selectTab('ws-tab-admin', dsID);
		}
	});
	
	// sync
	$("#ds-sync").live("click", function () {
		var dsID = $("#ws-selected-ds a").attr("href");
		busy();
		$.get(dsID + '/sync', function(data) {
			selectTab('ws-tab-status', dsID);
			done();
		});
	});

	// query data source
	$("#ds-exec-query").live("click", function () {
		var dsID = $("#ws-selected-ds a").attr("href");
		queryDatasource(dsID);
	});
	
	// remove data source
	$("#ds-delete").live("click", function () {
		var dsID = $("#ws-selected-ds a").attr("href");
		var confirmation = confirm('Are you sure that you want to delete the data source ' + dsID + "?");
		if(confirmation){
			removeDatasource(dsID);
		}
	});

	// access method selection
	$("#ds-access").live("change", function () {
		var method = $("#ds-access").val();
		if(method == 'sparql') {
			$("#ds-mode-field").hide('slow');
		}
		else {
			$("#ds-mode-field").show('slow');
		}
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
	var dsid = $("#ds-id").text();
	var method = $("#ds-access").val();
	
	if(method == 'sparql') {
		mode = 'remote';
	}
	else {
		mode = $("input:radio[name='ds-mode']:checked").val();
	}
	
	var dsdata = {
		name : $("#ds-name").val(),
		access_method : $("#ds-access").val(),
		access_uri : $("#ds-access-uri").val(),
		access_mode : mode
	};
	var noun = "../api/datasource";
	
	if(dsid != '') {
		noun = dsid + "/";
	}
	
	busy();
	
	$.ajax({
		type: "POST",
		url: noun,
		data: "dsdata="+ $.toJSON(dsdata),
		success: function(data){
			listDatasources();
			done();
		},
		error:  function(msg){
			alert(msg);
		} 
	});
}

function queryDatasource(dsid){
	var querydata = {
		query_str : $("#ds-query-str").val()
	};
	
	busy();
	$.ajax({
		type: "POST",
		url: dsid + "/query",
		data: "querydata="+ $.toJSON(querydata),
		success: function(data){
			$("#query-result").html(data);
			done();
		},
		error:  function(msg){
			alert(msg);
		} 
	});
}

function removeDatasource(dsid){
	
	busy();
	$.ajax({
		type: "POST",
		url: dsid + "/rm",
		success: function(data){
			$("#workspace").html("");
			listDatasources();
			done();
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
			$("#ds-delete-field").show();
		});
		// set form values
		$.getJSON(dsID, function(data) {
			$("#ws-selected-ds").html("<a href='" + data.id + "'>" + data.name + "</a>");
			$("#ds-id").text(data.id);
			$("#ds-name").val(data.name);
			$("#ds-access option[value='" + data.access_method + "']").attr("selected", true);
 			$("#ds-access-uri").val(data.access_uri);
			$("input:radio[name='ds-mode'][value='" + data.access_mode +"']").attr('checked', true);
			if(data.access_method == 'sparql') {
				$("#ds-mode-field").hide('fast');
			}
			else {
				$("#ds-mode-field").show('fast');
			}
			$("#ds-last-update").text("Last change: " + dateFormat(data.updated));
		});
		return;
	}

	if(tabID == "ws-tab-status") {
		$.get("forms/ds-status.html", function(data) {
			$("#ws-main").html(data);
		});
		// set form values
		$.getJSON(dsID, function(data) {
			// TODO: use http://www.datejs.com/ for pretty datetime formatting
			if(data.access_mode == 'local') {
				$("#ds-last-sync-field").show();
				$("#ds-last-sync").text(data.last_sync);
			}
			else {
				$("#ds-last-sync-field").hide();
			}
			if(!data.num_triples || data.num_triples == 0) {
				$("#ds-num-triples").text("Unknown - remote source or not synced, yet.");
			}
			else {
				if(!data.delta_triples || data.delta_triples == 0) {
					$("#ds-num-triples").text(data.num_triples);
				}
				else {
					if(data.delta_triples < 0) {
						$("#ds-num-triples").html(data.num_triples + "<span class='lesstriples' title='since last sync'>" + data.delta_triples + "</span>");
					}
					else {
						$("#ds-num-triples").html(data.num_triples + "<span class='moretriples' title='since last sync'>+" + data.delta_triples + "</span>");
					}
				}
			}
		});
		return;
	}
	
	$.get(tabMap[tabID], function(data) {
		$("#ws-main").html(data);
	});
}

function busy(){
	var oldtext = $("#pane-head").text();
	$("#pane-head").html("<img src='img/busy.gif' alt='busy' /><span style='display:none'>" + oldtext + "</span>");
}

function done(){
	var oldtext = $("#pane-head span").text();
	$("#pane-head").html(oldtext);
}

function dateFormat(datetimestr){
	if(!datetimestr || datetimestr == "") {
		return "unknown";
	}
	else {
		var d = new Date(datetimestr);
		var today = new Date();
		var m = d.getMinutes();
		var s = d.getSeconds();
		var year = d.getFullYear();
		var month = d.getMonth();
		var day = d.getDate();
		var date = "";
		
		if(year == today.getFullYear() && month == today.getMonth() && day == today.getDate()) {
			date = "Today ";
		}
		else{
			if(month < 9) month = "0" + month;
			date = year + "-" + month + "-" + day;
		}
		
		if(s < 10) s = "0" + s;
		if(m < 10) m = "0" + m;
		
		
		return date + " at " + d.getHours() + ":" + m + ":" + s;
	}
}


