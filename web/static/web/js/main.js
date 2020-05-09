// QUERY PARAMS
function getUrlParameter(name) {
   name = name.replace(/[\[]/, '\\]');
   var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
   var results = regex.exec(location.search);
   return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// NAV
toggleNav = () => {
	// e = document.getElementById("nav-menu-m");
	// e.classList.toggle("d-none");
	const e = document.getElementById("nav-menu");
	// e.classList.toggle("d-none");
	e.classList.toggle("nav__menu__open");
}

navMenuOpen = () => {
	const e = document.getElementById("nav-menu");
	e.classList.add("nav__menu__open");
}

navMenuClose = () => {
	const e = document.getElementById("nav-menu");
	e.classList.remove("nav__menu__open");
}

onOpenSearch = () => {
	const form = document.getElementById("search-form");
	const button = document.getElementById("search-open");
	const menu_toggle = document.getElementById("nav-toggle");
	form.classList.add("nav__search-opened");
	button.classList.add("d-none");
	menu_toggle.classList.add("d-none");

}

onCloseSearch = () => {
	const form = document.getElementById("search-form");
	const button = document.getElementById("search-open");
	const menu_toggle = document.getElementById("nav-toggle");
	form.classList.remove("nav__search-opened");
	button.classList.remove("d-none");
	menu_toggle.classList.remove("d-none");
}

navMenuDesktopToggle = () => {
	const toggle = document.getElementById("navdesktopmenu-toggle");
	const menu = document.getElementById("navdesktop-menu");
	menu.classList.toggle("nav__desktop-menu--open");
}

toggleCategories = () => {
	const cat_list = document.getElementById("cat-list")
	const header_drop = document.getElementById("header-drop");
	cat_list.classList.toggle("sidebar__guide__closed");
	
	if (header_drop.classList.contains("fa-angle-down")) {
		header_drop.classList.replace("fa-angle-down", "fa-angle-up");
	} else {
		header_drop.classList.replace("fa-angle-up", "fa-angle-down");
	}
}

// LIKE AND DISLIKE
function like() {
	const watch_id = $('#watch_id').val();
	const csrftoken = $("[name=csrfmiddlewaretoken").val();
	const btn_like = $('#btn-like');
	const btn_dislike = $('#btn-dislike');
	const like_counter = $('#like-counter');
	const dislike_counter = $('#dislike-counter');

	btn_like.toggleClass('active');
	btn_dislike.removeClass('active');
	btn_like.attr('disabled', true);
	btn_dislike.attr('disabled', true);

	$.ajax({
		type: 'POST',
		url: '/api/like',
		data: {'watch_id' : watch_id},
		beforeSend: function (request) {
			request.setRequestHeader("X-CSRFToken", csrftoken);
		},
		success: function (result) {
			console.log(result);
			like_counter.html(result['likes']);
			dislike_counter.html(result['dislikes']);
			updateLikebar(result['likes'], result['dislikes']);
		},
		error: function (result) {
			console.log(result);
		},
		complete: function (result) {
			btn_like.attr('disabled', false);
			btn_dislike.attr('disabled', false);
		}
	});
}

function dislike() {
	const watch_id = $('#watch_id').val();
	const csrftoken = $("[name=csrfmiddlewaretoken").val();
	const btn_like = $('#btn-like');
	const btn_dislike = $('#btn-dislike');
	const like_counter = $('#like-counter');
	const dislike_counter = $('#dislike-counter');
	btn_dislike.toggleClass('active');
	btn_like.removeClass('active');
	btn_like.attr('disabled', true);
	btn_dislike.attr('disabled', true);

	$.ajax({
		type: 'POST',
		url: '/api/dislike',
		data: {'watch_id': watch_id},
		beforeSend: function (request) {
			request.setRequestHeader("X-CSRFToken", csrftoken);
		},
		success: function (result) {
			console.log(result);
			like_counter.html(result['likes']);
			dislike_counter.html(result['dislikes']);
			updateLikebar(result['likes'], result['dislikes']);
		},
		error: function (result) {
			console.log(result);
		},
		complete: function (result) {
			btn_like.attr('disabled', false);
			btn_dislike.attr('disabled', false);
		}
	});
}

function updateLikebar(likes, dislikes) {
	var val = 50;
	rating = likes + dislikes;
	if (rating > 0) {
		val = (100 / (likes + dislikes)) * likes;
	}
	$('#likebar').width(val);
}

// PANEL DETAILS EXPANDER
function toggleExpander() {
	$('#panel-details').toggleClass('panel__details--collapsed');
}

// SUBSCRIBE

function toggleSubscribe() {
	const btn_sub = $('#btn-subscribe');
	const btn_sub_text = $('#btn-subscribe-text');
	const sub_counter = $('#sub-count');
	const channel_id = $('#channel_id').val();
	const csrftoken = $("[name=csrfmiddlewaretoken").val();

	btn_sub.attr('disabled', true);

	$.ajax({
		type: 'POST',
		url: '/api/subscribe',
		data: {'channel_id' : channel_id},
		beforeSend: function (request) {
			request.setRequestHeader("X-CSRFToken", csrftoken);
		},
		success: function (result) {
			console.log(result);
			if (btn_sub_text.html().trim() == 'Subscribe') {
				btn_sub_text.html(' Unsubscribe ');
			} else {
				btn_sub_text.html(' Subscribe ');
			}
			sub_counter.html(result['subscriber_count']);
		},
		error: function (result) {
			console.log(result);
		},
		complete: function (result) {
			btn_sub.attr('disabled', false);
		}
	});
}
