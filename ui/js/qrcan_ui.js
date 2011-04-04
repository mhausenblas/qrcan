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
	
	$("#all-ds").click(function () {
		$.get("forms/all-ds-work.html", function(data) {
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
	
	// schema sample for data source
	$("table.sresult td").live("click", function () {
		var typeURI = $(this).attr("resource");
		var dsID = $(this).parent().attr("resource");
		//alert( dsID + " - " + typeURI);
		$("table.sresult td").each(function() {
			$(this).removeClass("active-selection");
		});
		
		$(this).addClass("active-selection");
		sampleDatasource(dsID, typeURI);
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
		if(data){
			for(i in data) {
				var ds = data[i];
				b += "<div class='datasource' resource='" + ds["id"] + "'><img src='img/ds.png' alt='Data source ...' title='Data source ...' /> " + ds["name"] + "</div>";
			}
			$("#datasources").html(b);
			if(data[0]) $("#all-ds").show();
		}
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
		dataType: 'json',
		data: "querydata="+ $.toJSON(querydata),
		success: function(data){
			var b = "No results found";
			if(data[0] != 'none') {
				b ="<table class='qresult'><tr>";
				for(v in data[0]) {
					var variable = data[0][v];
					b += "<th>" + variable + "</th>";
				}
				b += "</tr>";
				for(r in data[1]) {
					var row = data[1][r];
					b += "<tr>";
					for(v in data[0]) {
						var variable = data[0][v];
						b += "<td>" + row[variable].value + "</td>";
					}
					b += "</tr>";
				}
				b += "</table>";
			}
			$("#query-result").html(b);
			done();
		},
		error:  function(msg){
			alert(msg);
		} 
	});
}

function sampleDatasource(dsid, turi){
	var sampledata = {
		type_uri : turi
	};
	
	busy();
	$.ajax({
		type: "POST",
		url: dsid + "/schema",
		dataType: 'json',
		data: "sampledata="+ $.toJSON(sampledata),
		success: function(data){
			var b = "No samples found.";
			if(data) {
				b = "";
				for(var r in data) {
					var row = data[r];
					for(var c in row) {
						b += "<div class='ds-entity-sample-details'> [ " + c +" ]&rarr; " + row[c] + "</div>";
					}
				}
			}
			$("#ds-entity-selection").html(b);
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

	// data source level:
	if(tabID == "ws-tab-query") {
		$.get("forms/ds-query.html", function(data) {
			$("#ws-main").html(data);
		});
		return;
	}

	if(tabID == "ws-tab-status") {
		$.get("forms/ds-status.html", function(data) {
			$("#ws-main").html(data);
		});
		// set form values
		$.getJSON(dsID, function(data) {
			if(data.access_mode == 'local') {
				$("#ds-last-sync-field").show();
				$("#ds-last-sync").text(dateFormat(data.last_sync));
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

	if(tabID == "ws-tab-schema") {
		busy();
		
		$.get("forms/ds-schema.html", function(data) {
			$("#ws-main").html(data);
		});
		$.getJSON(dsID + "/schema", function(data) {
			var b = "No schema info available";
			if(data) {
				b ="<table class='sresult'><tr><th>Entity type</th></tr>";
				for(var r in data) {
					var row = data[r];
					for(var c in row) {
						b += "<tr resource='" + dsID +"'>";
						b += "<td class='sampletype' resource='" + row[c] +"'>" + row[c] + " (" + c + ")</td>";
						b += "</tr>";
					}
				}
				b += "</table>";
			}
			$("#ds-entity-overview").html(b);
			done();
		});
		return;
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

	// all data sources:
	
	if(tabID == "ws-tab-export"){
		$.get("forms/ds-export.html", function(data) {
			$("#ws-main").html(data);
		});
		$.getJSON("../api/datasource/all", function(data) {
			var b = "";
			if(data){
				for(i in data) {
					var ds = data[i];
					b += "<div class='ds-all-selection-field'><input type='checkbox' value='" + ds["id"] + "' />" + ds["name"] + "</div>";
				}
				$("#ds-all-selection").html(b);
			}
		});
		return;
	}

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


