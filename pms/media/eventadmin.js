window.onload = function(){
var link = document.createElement('a');
var input = document.getElementById("id_url");
var url = input.value;
if (url.indexOf("www.") > -1){
	link.setAttribute('href', url);
}
else{
	link.setAttribute('href', 'http://www.assembly.org'+url);
}
link.innerHTML = "link";
console.log(link);
input.parentNode.appendChild(link);
};
