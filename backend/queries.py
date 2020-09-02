import random

from django.db.models import Sum, Count

from .models import Video, Category, Channel, Likes, Dislikes, Subscription, User, Image

def get_user(pk):
	return User.objects.get(pk=pk)

def get_latest_videos():
	return Video.published_objects.annotate(like_count=Count('likes__id'), sub_count=Count('channel__subscriptions__id')).order_by('-like_count', '-sub_count', '-views').filter(visibility__exact=Video.VisibilityStatus.PUBLIC)

def get_recommended_videos():
	videos = get_latest_videos()
	if videos:
		if videos.count() > 25:
			start = random.randint(0, videos.count()-21)
			return videos[start:start+20]
		else:
			return videos
	return None

def get_video(watch_id):
	try:
		return Video.objects.get(watch_id__exact=watch_id)
	except Video.DoesNotExist:
		return None

def get_published_video_or_none(watch_id):
	try:
		return Video.published_objects.get(watch_id__exact=watch_id)
	except Video.DoesNotExist:
		return None

def get_videos_from_channel(channel):
	return Video.published_objects.filter(channel__exact=channel, visibility__exact=Video.VisibilityStatus.PUBLIC)

def get_all_categories():
	return Category.objects.all()

def get_category(slug):
	return Category.objects.get(slug=slug)

def get_all_channels():
	return Channel.objects.all()

def get_channel(from_user):
	return Channel.objects.filter(user__exact=from_user)[0]

def get_channel_by_id(channel_id):
	return Channel.objects.filter(channel_id__exact=channel_id)[0]

def get_total_views(channel):
	return channel.videos.all().aggregate(Sum('views'))['views__sum'] or 0

def _get_likes(from_video):
	return Likes.objects.filter(video__exact=from_video).count()

def _get_dislikes(from_video):
	return Dislikes.objects.filter(video__exact=from_video).count()

def _remove_like(to_video, from_channel):
	like = Likes.objects.get(video=to_video, channel=from_channel)
	like.delete()

def _remove_dislike(to_video, from_channel):
	dislike = Dislikes.objects.get(video=to_video, channel=from_channel)
	dislike.delete()

def toggle_like(to_video, from_channel):
	if is_video_disliked(to_video, from_channel):
		_remove_dislike(to_video, from_channel)

	like = Likes.objects.filter(channel__exact=from_channel, video__exact=to_video)
	if like.exists():
		like[0].delete()
		return (_get_likes(to_video), _get_dislikes(to_video))

	Likes.objects.create(channel=from_channel, video=to_video)
	return (_get_likes(to_video), _get_dislikes(to_video))

def toggle_dislike(to_video, from_channel):
	if is_video_liked(to_video, from_channel):
		_remove_like(to_video, from_channel)

	dislike = Dislikes.objects.filter(channel__exact=from_channel, video__exact=to_video)
	if dislike.exists():
		dislike[0].delete()
		return (_get_likes(to_video), _get_dislikes(to_video))

	Dislikes.objects.create(channel=from_channel, video=to_video)
	return (_get_likes(to_video), _get_dislikes(to_video))

def is_video_liked(to_video, from_channel):
	return Likes.objects.filter(channel__exact=from_channel, video__exact=to_video).exists()

def is_video_disliked(to_video, from_channel):
	return Dislikes.objects.filter(channel__exact=from_channel, video__exact=to_video).exists()

def toggle_subscription(to_channel, from_channel):
	sub = Subscription.objects.filter(to_channel__exact=to_channel, from_channel__exact=from_channel)
	if sub.exists():
		sub[0].delete()
	else:
		Subscription.objects.create(from_channel=from_channel, to_channel=to_channel)
	return get_subscriber_count(to_channel)

def get_subscriber_count(channel):
	return Subscription.objects.filter(to_channel=channel).count() 

def is_subscribed(to_channel, from_channel):
	return Subscription.objects.filter(to_channel__exact=to_channel, from_channel__exact=from_channel).exists()

def increment_view_count(watch_id):
	video = get_video(watch_id)
	video.views += 1
	video.save()
	return video.views

def get_image_by_pk(pk):
	return Image.objects.get(pk=pk)