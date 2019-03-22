'use strict';

var debug_status = "default";

var update_status = function(){
    var info = $("#info");
    var status = $("#status");
    var debug_header = $("#debug-header");
    var status_icon = $("#status-icon");
    
    info.removeClass();
    status.removeClass();
    debug_header.removeClass();
    
    switch (debug_status){
        case "ok": 
            info.addClass("success");
            status.addClass("success");
            debug_header.addClass("success");
            
            status_icon.html("&#10004;");
            break;
        case "error":
            info.addClass("error");
            status.addClass("error");
            debug_header.addClass("error");
            
            status_icon.html("&#10007;");
            break;
        case "breaker-open":
            info.addClass("error");
            status.addClass("error");
            debug_header.addClass("error");
            
            status_icon.html("&#10007;");
            break;
        defualt:
            info.addClass("default");
            status.addClass("default");
            debug_header.addClass("default");
            
            status_icon.html("&#10004;");
            break;
    }
};

var update_debug = function(data){
    var status = $("#status");
    var info = $("#info-text");
    var debug_template = $('#debug-template').html();
    
    debug_status = data.status;
    
    status.html(data.status.toUpperCase());
    info.html(Mustache.render(debug_template, data));
};

var place_dog = function(url){
    var container = $("#dog");
    
    if (url.endsWith(".mp4") || url.endsWith(".webm")){
        var tag = $("<video controls muted></video>");
        var source = $("<source autoplay></source>");
        source.attr("src", url);
        tag.append(source);
        tag[0].play();
    } else {
        var tag = $("<img>");
        tag.attr("src", url);
    }
    
    container.empty();
    container.append(tag);
};

var error_dog = function(data){
    place_dog("images/error-peanut.jpg");
};

var load_dog = function(data){
    place_dog(data.dog.url);
    update_debug(data);
};

var failure = function(data){
   error_dog();
   update_debug(data.responseJSON);
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
    $(this).bind('ajaxStart', function(){
        $("#status-icon").html("<img id='loader' src='images/ajax-loader.gif'>");
    });
    $(this).bind('ajaxComplete', function(){
        update_status();
    });
    
    $("#dog img").on("load", function(event) {
       if ($(window).height() < event.target.naturalHeight) {
           $(event.target).css("flex-shrink", "1");
       } else {
           $(event.target).css("flex-shrink", "0");
       }
    });
});