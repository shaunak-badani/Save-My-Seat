var x,y;
x = [];
y = []
function bookSeat(i,cols)
{
	var a = document.getElementById(i);
	a.classList.remove('seat');
	a.classList.add('booking');
	a.onclick = function(){return false;};
	x.push(Math.floor(i/cols));
	y.push(i%cols);	
}
function sendData(lin)
{
	x = JSON.stringify(x)
	y = JSON.stringify(y)
	$.ajax({
		type:"POST",
		url : lin,
		datatype: "json",
		traditional:true,
		data : {
			"js_data" : x,
			"col_nos" : y
		}
	}).done(function(){ console.log("hi dear");
	window.location.href = '/checkout';});

}