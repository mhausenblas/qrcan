$(function() {
	listDatasources();
	
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
		$(".ws-tab").each(function() {
			$(this).removeClass("active-tab");
		});
		$(this).addClass("active-tab");
		selectTab(tabID);
	});
	
	// hoover effects
	$(".datasource").live("mouseover", function() {
		$(this).css("color", "#44A");
	}).live("mouseout", function() {
		$(this).css("color", "#000");
	});
	
	$(".cmdbtn").mouseover(function () {
		$(this).css("border", "1px solid #9f9f9f");
	}).mouseout(function(){
		$(this).css("border", "1px solid #f0f0f0");
	});
});

function listDatasources(){
	$.getJSON("../api/datasource/all", function(data) {
		var b = "";
		for(i in data) {
			var ds = data[i];
			b += "<div class='datasource' resource='" + ds["id"] + "'>" + ds["title"] + "</div>";
		}
		$("#datasources").html(b);
	});
}

function selectTab(tabID, dsID){
	var tabMap = { 
		"ws-tab-query" : "forms/ds-query.html",
		"ws-tab-status" : "forms/ds-status.html",
		"ws-tab-schema" : "forms/ds-schema.html",
		"ws-tab-export" : "forms/ds-export.html",
		"ws-tab-admin" : "forms/ds-admin.html"
	}
	
	$.get(tabMap[tabID], function(data) {
		$("#ws-main").html(data);
	});	
}