var width = 900,
    height = 85,
    cellSize = 10; // cell size
    weekdays = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
    month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
	
var day = d3.time.format("%w"),
    week = d3.time.format("%U"),
    percent = d3.format(".1%"),
	  format = d3.time.format("%Y-%m-%d");
parseDate = d3.time.format("%Y-%m-%d").parse;
		
/* var colorScale = d3.scale.linear()
    .range(["#fdfbf2", '#ff0000'])
    .domain([0, 4]) */
var colorScale = d3.scale.linear();
colors = ['#ffffcc','#a1dab4','#41b6c4','#2c7fb8','#253494'];
colors = ['#ffffd4','#fed98e','#fe9929','#d95f0e','#993404'];
colorScale.domain([0,1,2,3,4]).range(colors);
    
var svg = d3.select(".calender-map").selectAll("svg")
    .data(d3.range(2015, 2019))
    .enter().append("svg")
    .attr("width", '100%')
    .attr("data-height", '0.5678')
    .attr("viewBox",'0 0 900 85')
    .attr("class", "RdYlGn")
    .append("g")
    .attr("transform", "translate(" + ((width - cellSize * 53) / 2) + "," + (height - cellSize * 7 - 1) + ")");

svg.append("text")
    .attr("transform", "translate(-38," + cellSize * 3.5 + ")rotate(-90)")
    .style("text-anchor", "middle")
    .text(function(d) { return d; });
 
for (var i=0; i<4; i++) {    
  svg.append("text")
      .attr("transform", "translate(-5," + cellSize*(2*i+1) + ")")
      .style("text-anchor", "end")
      .attr("dy", "-.25em")
      .text(function(d) { return weekdays[2*i]; }); 
}

var rect = svg.selectAll(".day")
    .data(function(d) { return d3.time.days(new Date(d, 0, 1), new Date(d + 1, 0, 1)); })
    .enter().append("rect")
    .attr("class", "day")
    .attr("width", cellSize)
    .attr("height", cellSize)
    .attr("x", function(d) { return week(d) * cellSize; })
    .attr("y", function(d) { return day(d) * cellSize; })
    .attr("fill",'#fff')
    .datum(format);

var legend = svg.selectAll(".legend")
      .data(month)
      .enter().append("g")
      .attr("class", "legend")
      .attr("transform", function(d, i) { return "translate(" + (((i+1) * cellSize*4.2)+8) + ",0)"; });

legend.append("text")
   .attr("class", function(d,i){ return month[i] })
   .style("text-anchor", "end")
   .attr("dy", "-.25em")
   .text(function(d,i){ return month[i] });
   
svg.selectAll(".month")
    .data(function(d) { return d3.time.months(new Date(d, 0, 1), new Date(d + 1, 0, 1)); })
  .enter().append("path")
    .attr("class", "month")
    .attr("id", function(d,i){ return month[i] })
    .attr("d", monthPath);

d3.csv("static/data/calendar.txt", function(error, csv) {

  csv.forEach(function(d) {
    d.ct = parseInt(d.ct);
  });

  var ct_Max = d3.max(csv, function(d) { return d.count; });
 
  var data = d3.nest()
    .key(function(d) { return d.date; })
    .rollup(function(d) { return d[0].ct; })
    .map(csv);
	
  rect.filter(function(d) { return d in data; })
    .attr("fill", function(d) { return colorScale(data[d]); })
	  .attr("data-title", function(d) { return "Sales: "+data[d]});   
  $("rect").tooltip({container: 'body', html: true, placement:'top'}); 
  
});

function monthPath(t0) {
  var t1 = new Date(t0.getFullYear(), t0.getMonth() + 1, 0),
      d0 = +day(t0), w0 = +week(t0),
      d1 = +day(t1), w1 = +week(t1);
  return "M" + (w0 + 1) * cellSize + "," + d0 * cellSize
      + "H" + w0 * cellSize + "V" + 7 * cellSize
      + "H" + w1 * cellSize + "V" + (d1 + 1) * cellSize
      + "H" + (w1 + 1) * cellSize + "V" + 0
      + "H" + (w0 + 1) * cellSize + "Z";
}
