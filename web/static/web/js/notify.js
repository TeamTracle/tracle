var notify_badge_class;
var notify_menu_class;
var notify_api_url;
var notify_fetch_count;
var notify_unread_url;
var notify_mark_all_unread_url;
var notify_refresh_period = 15000;
var consecutive_misfires = 0;
var registered_functions = [];

function fill_notification_badge(data) {
    var badges = document.getElementsByClassName(notify_badge_class);
    if (badges) {
        for(var i = 0; i < badges.length; i++){
            badges[i].innerHTML = data.unread_count;
        }
    }
}

function fill_notification_list(data) {
    var menus = document.getElementsByClassName(notify_menu_class);
    if (menus) {
        var messages = data.unread_list.map(function (item) {
            var message = '';
            if (item.notification_type === 'CO') {
                message += comment_template(item);
            } else if (item.notification_type === 'VI') {
                message += video_template(item);
            } else if (item.notification_type === 'TA') {
                message += tag_template(item);
            }
            return message;
        }).join('')

        for (var i = 0; i < menus.length; i++){
            menus[i].innerHTML = messages;
        }
    }
}

function markReadAndOpen(event, id) {
    event.preventDefault();
    let target_url = event.currentTarget.href;
    let csrftoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    let data = new FormData()
    data.append('id', id);
    axios.post('/api/notifications', data, {headers: {'X-CSRFToken' : csrftoken, 'Content-Type': 'multipart/form-data'}})
    .then(response => {
        document.location = target_url;
    })
    .catch(error => {
        console.log(error.response);
        document.location = target_url;
    });
}

function comment_template(item) {
    message = '';
    message += '<a class="item" href="/watch?v=' + item.target_object.watch_id  + '#comment-' + item.action_object.id + '" onclick="markReadAndOpen(event, ' + item.id + ')"' + '>';
    message +=   '<img class="avatar" src="' + item.actor.avatar + '">';
    message +=   '<div class="action">';
    message +=     '<div class="action__text">';
    message +=       '' + item.actor.name + ' commented:<div style="white-space: nowrap;text-overflow: ellipsis;">' + item.action_object.text + '</div>';
    message +=     '</div>';
    message +=     '<div class="action__timestamp">';
    message +=       '' + item.created + ' ago';
    message +=     '</div>';
    message +=   '</div>';
    message +=   '' + '<img class="target" src="' + item.target_object.thumbnail + '">'
    message +='</a>';
    return message;
}

function video_template(item) {
    message = '';
    message += '<a class="item" href="/watch?v=' + item.action_object.watch_id + '" onclick="markReadAndOpen(event, ' + item.id + ')"' + '>';
    message +=   '<img class="avatar" src="' + item.actor.avatar + '">';
    message +=   '<div class="action">';
    message +=     '<div class="action__text">';
    message +=       '' + item.actor.name + ' uploaded: ' + item.action_object.title;
    message +=     '</div>';
    message +=     '<div class="action__timestamp">';
    message +=       '' + item.created + ' ago';
    message +=     '</div>';
    message +=   '</div>';
    message +=   '<img class="target" src="' + item.action_object.thumbnail + '">';
    message += '</a>';
    return message;
}

function tag_template(item) {
    message = '';
    message += '<a class="item" href="/watch?v=' + item.target_object.watch_id  + '#comment-' + item.action_object.id + '" onclick="markReadAndOpen(event, ' + item.id + ')"' + '>';
    message +=   '<img class="avatar" src="' + item.actor.avatar + '">';
    message +=   '<div class="action">';
    message +=     '<div class="action__text">';
    message +=       '' + item.actor.name + ' tagged you';
    message +=     '</div>';
    message +=     '<div class="action__timestamp">';
    message +=       '' + item.created + ' ago'; 
    message +=     '</div>';
    message +=   '</div>';
    message +=   '</div><img class="target" src="' + item.target_object.thumbnail + '">';
    message += '</a>';
    return message;
}

function register_notifier(func) {
    registered_functions.push(func);
}

function fetch_api_data() {
    if (registered_functions.length > 0) {
        //only fetch data if a function is setup
        var r = new XMLHttpRequest();
        r.addEventListener('readystatechange', function(event){
            if (this.readyState === 4){
                if (this.status === 200){
                    consecutive_misfires = 0;
                    var data = JSON.parse(r.responseText);
                    registered_functions.forEach(function (func) { func(data); });
                }else{
                    consecutive_misfires++;
                }
            }
        })
        r.open("GET", notify_api_url+'?status=unread', true);
        r.send();
    }
    if (consecutive_misfires < 10) {
        setTimeout(fetch_api_data,notify_refresh_period);
    } else {
        var badges = document.getElementsByClassName(notify_badge_class);
        if (badges) {
            for (var i = 0; i < badges.length; i++){
                badges[i].innerHTML = "!";
                badges[i].title = "Connection lost!"
            }
        }
    }
}

setTimeout(fetch_api_data, 1000);