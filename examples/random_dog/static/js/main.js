/************************************
 Javascript for random_dog example.
 
 Uses JQuery and Mustache.
 
*************************************/ 
'use strict';

// global state of the remote breaker, used for the debug section.
var debug_status = "default";

/***
 Handle the debug info from the breaker.
 
 Changes the icon next to "Random Dog!", and also changes some classes so you get
 a color difference depending on the state of the breaker.
***/
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

/***
 Processes the debugging info containing state details about the breaker,
 and updates the information area.
 
 Uses the #debug-template mustache template for display.
***/
var update_debug = function(data){
    var status = $("#status");
    var info = $("#info-text");
    var debug_template = $('#debug-template').html();
    
    debug_status = data.status;
    
    status.html(data.status.toUpperCase());
    info.html(Mustache.render(debug_template, data));
};

/***
 Processes the URL returned from the back-end.
 
 Places the image or video in the display area.
***/
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

/***
 Place a special image when there's a back-end error.
***/
var error_dog = function(data){
    place_dog("images/error-peanut.jpg");
};

/***
 Handle a successful response from the back-end
***/
var load_dog = function(data){
    place_dog(data.dog.url);
    update_debug(data);
};

/*** 
 Handle a failure from the back-end
***/
var failure = function(data){
   error_dog();
   update_debug(data.responseJSON);
};

/***
 Make a request for another random dog
***/
var next_dog = function(){
    $.ajax({
        type: "get",
        url: "/dog",
        success: load_dog,
        error: failure});
};

/***
 Setup
***/
$(document).ready(function() {
    // click the "new dog" button, get a new dog.
    $("#next").on("click", next_dog);
    
    // display the "loading" pac-man image when ajax is happening.
    $(this).bind('ajaxStart', function(){
        $("#status-icon").html("<img id='loader' src='images/ajax-loader.gif'>");
    });
    $(this).bind('ajaxComplete', function(){
        update_status();
    });
    
    // handle some wonkiness with images of different aspect ratios
    $("#dog img").on("load", function(event) {
       if ($(window).height() < event.target.naturalHeight) {
           $(event.target).css("flex-shrink", "1");
       } else {
           $(event.target).css("flex-shrink", "0");
       }
    });
});