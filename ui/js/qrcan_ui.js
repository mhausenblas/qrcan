$(function() {

	$("#ds-refresh").click(function () {
		$("#workspace").html("");
		$.getJSON("../api/datasource/all", function(data) {
			var b = "";
			for(i in data) {
				var ds = data[i];
				b += "<a href='" + ds["id"] + "'>" + ds["title"] + "</a> <br />";
			}
			$("#datasources").html(b);
		});
	});
	
	$("#ds-add").click(function () {
		$.get("forms/ds-add.html", function(data) {
		  $("#workspace").html(data);
		});
	});
	
	$(".cmdbtn").mouseover(function () {
		$(this).css("border", "1px solid #9f9f9f");
	}).mouseout(function(){
		$(this).css("border", "1px solid #f0f0f0");
	});
});