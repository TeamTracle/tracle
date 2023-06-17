import random
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Sum, Count
from django.utils import timezone

from .models import Video, Category, Channel, Likes, Dislikes, Subscription, User, Image, CommentLike, CommentDislike, Comment

def get_user(pk):
	return User.objects.get(pk=pk)

def get_top_videos():
	videos = cache.get('topvideos')
	if not videos:
		videos = Video.objects.public()\
			.annotate(
				like_count=Count('likes__id'),
				sub_count=Count('channel__subscriptions__id'))\
			.order_by('-like_count', '-sub_count', '-views_sum', '-created')
		if videos:
			if videos.count() > 60:
				start = random.randint(0, 40)
				videos = list(videos[start:start+20])
				random.shuffle(videos)
			for v in videos:
				setattr(v, 'thumbnail_url', v.get_thumbnail())
			cache.set('topvideos', videos, timeout=3600)

	return videos

def get_latest_videos():
	videos = cache.get('latestvideos')
	if not videos:
		videos = Video.objects.public().order_by('-created').filter(views__gt=10)
		videos = list(videos[0:min(videos.count(), 50)])
		for v in videos:
			setattr(v, 'thumbnail_url', v.get_thumbnail())
		random.shuffle(videos)
		cache.set('latestvideos', videos, timeout=3600)

	return videos

def get_videos_from_category(category):
	videos = cache.get(f'{category.slug}_videos')
	if not videos:
		videos =  Video.objects.public().filter(category=category).order_by('-created')
		for v in videos:
			setattr(v, 'thumbnail_url', v.get_thumbnail())
		cache.set(f'{category.slug}_videos', videos, timeout=3600)
	return videos


def get_recommended_videos():
	videos = Video.objects.public()
	if videos:
		videos = list(videos)

		if len(videos) > 25:
			start = random.randint(0, len(videos)-21)
			videos = videos[start:start+20]

		for v in videos:
			setattr(v, 'thumbnail_url', v.get_thumbnail())

		return videos
	else:
		return None

def get_video(watch_id):
	try:
		return Video.objects.get(watch_id__exact=watch_id)
	except Video.DoesNotExist:
		return None

def get_published_video_or_none(watch_id):
	try:
		video = Video.objects.public().get(watch_id__exact=watch_id)
		return video
	except Video.DoesNotExist:
		return None

def get_videos_from_channel(channel):
	return Video.objects.public().filter(channel__exact=channel, visibility__exact=Video.VisibilityStatus.PUBLIC)

def filter_by_search_terms(search_terms):
	return Video.objects.search(search_terms)

def get_sub_feed(channel):
	videos = cache.get(f'{channel.channel_id}_subfeed')
	if not videos:
		subs = channel.subscribers.all()
		videos = Video.objects.filter(channel__in=[ sub.to_channel for sub in subs.all() ]).order_by('-created')
		for v in videos:
			setattr(v, 'thumbnail_url', v.get_thumbnail())
		cache.set(f'{channel.channel_id}_subfeed', videos, timeout=3600)
	return videos

def get_all_categories():
	return Category.objects.all()

def get_category(slug):
	return Category.objects.get(slug=slug)

def get_all_channels():
	return Channel.objects.filter(user__banned=False)

def get_channel(from_user):
	return Channel.objects.filter(user__exact=from_user)[0]

def get_channel_by_id(channel_id):
	try:
		return Channel.objects.get(channel_id=channel_id, user__banned=False)
	except Channel.DoesNotExist:
		return None

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

def is_comment_liked(comment, channel):
	return CommentLike.objects.filter(comment__exact=comment, channel__exact=channel).exists()

def _remove_comment_like(comment, channel):
	like = CommentLike.objects.get(comment=comment, channel=channel)
	like.delete()

def is_comment_disliked(comment, channel):
	return CommentDislike.objects.filter(comment__exact=comment, channel__exact=channel).exists()

def _remove_comment_dislike(comment, channel):
	dislike = CommentDislike.objects.get(comment=comment, channel=channel)
	dislike.delete()

def toggle_comment_like(comment, channel):
	if is_comment_disliked(comment, channel):
		_remove_comment_dislike(comment, channel)

	like = CommentLike.objects.filter(comment=comment, channel=channel)
	if like.exists():
		like[0].delete()
		return (comment.likes.count(), comment.dislikes.count())

	CommentLike.objects.create(comment=comment, channel=channel)
	return (comment.likes.count(), comment.dislikes.count())


def toggle_comment_dislike(comment, channel):
	if is_comment_liked(comment, channel):
		_remove_comment_like(comment, channel)

	dislike = CommentDislike.objects.filter(comment=comment, channel=channel)
	if dislike.exists():
		dislike[0].delete()
		return (comment.likes.count(), comment.dislikes.count())

	CommentDislike.objects.create(comment=comment, channel=channel)
	return (comment.likes.count(), comment.dislikes.count())

def get_comment(pk):
	return Comment.objects.get(pk=pk)