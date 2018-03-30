var audio = new Audio('change_screen.ogg');
var color = ['#ee6675','#00979a','#e64d40','#009667','#85c553','#814a74','#f58239'];var current_color=0;

$(document).ready(
    function() {
        FastClick.attach(document.body);
    }
);

/***
DISPLAY MANAGER: displays the right content
***/
var current_displayed_state = "Loading";
function display_state(new_state){
    if(new_state == current_displayed_state) {
        console.log("Display state "+new_state+" which is already displayed, doing nothing.")
    }
    console.info("display state: "+new_state);
    $("#content_div").children().hide();
    if(new_state == "content_ready_div") {
        $(".to_hide_when_not_ready").show();
    } else {
        $(".to_hide_when_not_ready").hide();
    }
    $("#"+new_state).show();
}
var current_page_displayed = "Home";
function display_page(new_page) {
    if(new_page == current_page_displayed) {
        console.log("Display page "+new_page+" which is already displayed, doing nothing.")
    }
    console.info("display page: "+new_page);
    $("#content_ready_div").children().hide();
    if(new_page != "dynamic_pageHome_div") {
        $("#button_home").show();
    } else {
        $("#button_home").hide();
    }
    $("#"+new_page).show();
}
function display_mute_button() {
    $("#button_unmute").hide();
    $("#button_mute").show();
}
function display_unmute_button() {
    $("#button_mute").hide();
    $("#button_unmute").show();
}
function display_apps_names(display) {
    if(display){
        $(".dynamic_page_app_button>div").show();
    } else {
        $(".dynamic_page_app_button>div").hide();
    }
}

/***
PAGES MANAGER: creates the pages
***/

function make_color(){
	//To get color from the list in random order
	// var new_color = color[Math.floor(Math.random() * color.length)];
   var new_color = color[current_color];
   current_color += 1;
   if(current_color==color.length) current_color=0;
   return new_color;
}
function add_app_to_full_apps_list(id, launch_path, icon, name) {
    var element_id = "dynamic_all_apps_app_"+id;
    var div_id = element_id+'_div'
    var image_id = element_id+'_img'
    var name_id = element_id+'_name'

    // Add containers for app's name and app's icon
    $("#footer_all_apps_dropdown").append(
        '<div id="'+div_id+'" class="dynamic_all_apps_dropdown_app_div">'+
            '<img id="'+image_id+'" class="gridImg" src="'+icon+'"/>'+
            '<div id="'+name_id+'" class="behaviorNameGrid">'+name+'</div>'+
        '</div>');
    $("#"+div_id).off('click');
    $("#"+div_id).on('click', function(){
        $("#"+div_id).blur();
        audio.play();
        requestRunBehavior(launch_path);
    });
}
function add_app_to_page(page_div_id, app_id, name, launch_path, icon) {
    // Add app button
    var nbApps = $("#"+page_div_id).find(".dynamic_page_app_button").length;
    var line=1;
    if(nbApps%2 == 1) line=2;
    var parent_div_class = "#"+page_div_id+" .dynamic_page_line"+line+"_div"
    var app_button_id = page_div_id+"_button"+app_id
    $(parent_div_class).append(''+
        '<div id="'+app_button_id+'" class="dynamic_page_app_button">'+
            '<img src="'+icon+'"/>'+
            '<div>'+name+'</div>'+
        '</div>');

    // add button action on click
    $("#"+app_button_id).off('touchmove click');
    $("#"+app_button_id).on('touchmove click', function(){
        $("#"+app_button_id).blur();
        audio.play();
        requestRunBehavior(launch_path);
    });

    // make sure icons are aligned correctly depending on how many are on each line
    var nbButtonsLine1 = $("#"+page_div_id+" .dynamic_page_line1_div").children().length;
    var nbButtonsLine2 = $("#"+page_div_id+" .dynamic_page_line2_div").children().length;
    if((nbButtonsLine1-nbButtonsLine2)%2 == 0) {
        $("#"+page_div_id+" .dynamic_page_line2_div").addClass("line2_div_right");
    } else {
        $("#"+page_div_id+" .dynamic_page_line2_div").removeClass("line2_div_right");
    }
}
function add_page(id, name, apps) {
    //console.log("Adding page "+id)
    var identifier = "dynamic_page"+id

    // Add the page div
    var page_div_id = identifier+'_div';
    $("#content_ready_div").append(
        '<div id="'+page_div_id+'" style="display:none">'+
            '<div class="dynamic_page_line1_div"></div>'+
            '<div class="dynamic_page_line2_div"></div>'+
        '</div>');

    // Add apps to the page
    for(var app_id in apps) {
        var app_name = apps[app_id]["name"];
        var launch_path = apps[app_id]["uuid"]+"/"+apps[app_id]["behavior_path"];
        var icon = apps[app_id]["icon"];
        add_app_to_page(page_div_id, app_id, app_name, launch_path, icon);
    }

    // Add page button on home page
    var nbButtons = $(".dynamic_pageHome_app_button").length;
    var line=1;
    if(nbButtons%2 == 1) line=2;
    var parent_div_class = "#dynamic_pageHome_div .dynamic_pageHome_line"+line+"_div"
    var button_div_id = "content_ready_pageHome_button_"+id
    $(parent_div_class).append(
        '<div id="'+button_div_id+'" class="dynamic_pageHome_app_button">'+
        '   <div>'+name+'</div>'+
        '</div>');
    $('#'+button_div_id).children().css('background-color', make_color());

    // add home button action on click
    $("#"+button_div_id).off('touchmove click');
    $("#"+button_div_id).on('touchmove click', function(){
        $("#"+button_div_id).blur();
        audio.play();
        requestPage(id);
    });

    // make sure icons are aligned correctly depending on how many are on each line
    var nbButtonsLine1 = $("#dynamic_pageHome_div .dynamic_pageHome_line1_div").children().length;
    var nbButtonsLine2 = $("#dynamic_pageHome_div .dynamic_pageHome_line2_div").children().length;
    if((nbButtonsLine1-nbButtonsLine2)%2 == 0) {
        $("#dynamic_pageHome_div .dynamic_pageHome_line2_div").addClass("line2_div_right");
    } else {
        $("#dynamic_pageHome_div .dynamic_pageHome_line2_div").removeClass("line2_div_right");
    }


}

/***
CALLBACKS TO REACT TO APPLAUNCHER SIGNALS
***/

// Declare all callbacks
function onCurrentStateChanged(state, behaviorName) {
    // AppLauncher state can be ready, running, sleeping
    // if no state, display a spinner.
    console.log("State changed: " + state);
    if (state == "ready") display_state("content_ready_div");
    else if (state == "running") { }
    else if (state == "sleeping")   display_state("content_sleeping_div");
    else display_state("content_loading_div");
}
function onCurrentPageChanged(new_page_displayed) {
    console.info("Page to display: "+new_page_displayed);
    display_page("dynamic_page"+new_page_displayed+"_div")
}
function onAppFullListChanged(new_app_list) {
    console.info("New app list")
    //console.info(new_app_list)
    $("#footer_all_apps_dropdown").html("");
    for (var id in new_app_list) {
        var launch_path = new_app_list[id]["uuid"]+"/"+new_app_list[id]["behavior_path"]
        var name = new_app_list[id]["name"]
        var icon_url = new_app_list[id]["icon"]
        add_app_to_full_apps_list(id, launch_path, icon_url, name);
    }
}
function onPagesDefinitionChanged(new_page_definition) {
    console.info("New pages definition")
    //console.info(new_page_definition)
    $("#content_ready_div").html(
        '<div id="dynamic_pageHome_div">'+
             '<div class="dynamic_pageHome_line1_div"></div>'+
             '<div class="dynamic_pageHome_line2_div"></div>'+
        '</div>');
    for (var id in new_page_definition) {
        var name = new_page_definition[id]["title"]
        var apps = new_page_definition[id]["apps"]
        add_page(id, name, apps);
    }
}
function onAutonomousEnabledChanged(state) {
    console.log("Robot is proactive:"+state);
    if(state) {
        display_mute_button();
    } else {
        display_unmute_button();
    }
}
function onDisplayAppNameChanged(state) {
    display_apps_names(state);
}
function onPingRequired(max_delay) {
    console.log("Ping required before "+max_delay+"s.");
    ping();

}

// Connect signals with callbacks
session.service("AppLauncher").then(
    function(ap) {
        ap.current_state.connect(onCurrentStateChanged);
        ap.current_page.connect(onCurrentPageChanged);
        ap.apps_full_list.connect(onAppFullListChanged);
        ap.pages_definition.connect(onPagesDefinitionChanged);
        ap.autonomous_enabled.connect(onAutonomousEnabledChanged);
        ap.display_app_name.connect(onDisplayAppNameChanged);
        ap.ping_required.connect(onPingRequired);
    }
);

// Initialize all states
$(document).ready(
    function(){
        session.service("AppLauncher").then( function(ap) {
            ap.current_state.value().then(onCurrentStateChanged);
            ap.current_page.value().then(onCurrentPageChanged);
            ap.apps_full_list.value().then(onAppFullListChanged);
            ap.pages_definition.value().then(onPagesDefinitionChanged);
            ap.autonomous_enabled.value().then(onAutonomousEnabledChanged);
            ap.display_app_name.value().then(onDisplayAppNameChanged);
            onPingRequired(2);
        });
    }
);

/***
FUNCTIONS TO CALL APPLAUNCHER METHODS
***/

// Declare all functions
function ping() {
    console.log("Ping AppLauncher service asking a 5s delay before next request.");
    session.service("AppLauncher").then( function(ap) {
        ap.ping(5);
    });
}
function requestPage(page_id){
    console.log("Requesting page change to page: "+page_id);
    session.service("AppLauncher").then( function(ap) {
        ap.current_page.setValue(page_id);
    });
}
function requestVolumeChange(diff){
    console.log("Requesting volume change: "+diff);
    session.service("AppLauncher").then( function(ap) {
        ap.adjustVolume(diff);
    });
}
function requestAutonomousEnabled(state){
    console.log("Request autonomous to be: ", state);
    session.service("AppLauncher").then( function(ap) {
        ap.autonomous_enabled.setValue(state);
    });
}
function requestRunBehavior(launch_path) {
    console.info("Request run behavior: "+launch_path);
    session.service("AppLauncher").then( function(ap) {
        ap.runBehavior(launch_path);
    });
}

// Connect buttons with functions
$(document).ready(
    function() {
        $('#button_home').on('touchmove click', function(){
            requestPage("Home");
        });
        $('#button_volume_up').on('touchmove click', function(e){
            requestVolumeChange(20);
            e.stopPropagation();
        });
        $('#button_volume_down').on('touchmove click', function(e){
            requestVolumeChange(-20);
            e.stopPropagation();
        });
        $('#button_unmute').on('touchmove click', function(e){
            requestAutonomousEnabled(true);
            e.stopPropagation();
        });
        $('#button_mute').on('touchmove click', function(e){
            requestAutonomousEnabled(false);
            e.stopPropagation();
        });
        $('button').on("click", function(){
            this.blur();
            audio.play();
        });
    }
);
