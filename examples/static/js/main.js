'use strict';

var update_debug = function(data){
    var info = $("#debug-info");
    var status = $("#status");
    var debug_template = $('#debug-template').html();
     
    status.html(data.status);
    
    info.html(Mustache.render(debug_template, data));
};

var load_dog = function(data){
    var container = $("#dog");
    
    if (data.dog.url.endsWith(".mp4")){
        var tag = $("<video controls></video>");
        var source = $("<source autoplay></source>");
        source.attr("src", data.dog.url);
        tag.append(source);
        tag.play();
    } else {
        var tag = $("<img>");
        tag.attr("src", data.dog.url);
    }
    
    container.empty();
    container.append(tag);
    
    update_debug(data);
    
    console.log(data);
};

var failure = function(data){
    update_debug(JSON.parse(data.response));
};

var next_dog = function(){
    $.ajax({
        type: "get",
        url: "/dog",
        success: load_dog,
        error: failure});
};


$(document).ready(function() {
    $("#next").on("click", next_dog);
});