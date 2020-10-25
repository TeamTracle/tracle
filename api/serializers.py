import magic

from django.utils.timesince import timesince

from rest_framework import serializers

from backend.models import Video, Comment, Channel, Subscription, Notification

class VideoSerializer(serializers.ModelSerializer):
	thumbnail = serializers.CharField(source='get_thumbnail')
	# status = serializers.CharField(source='get_video_status')

	class Meta:
		model = Video
		fields = ['pk', 'watch_id', 'title', 'description', 'thumbnail', 'created', 'views', 'likes', 'dislikes', 'visibility', 'transcode_status', 'published']


class VideoEditSerializer(serializers.ModelSerializer):
	class Meta:
		model = Video
		fields = ['title', 'description', 'category', 'visibility']

	def update(self, instance, validated_data):
		print(validated_data.get('visibility'))
		instance.category = validated_data.get('category', instance.category)
		instance.description = validated_data.get('description', instance.description)
		instance.title = validated_data.get('title', instance.title)
		instance.visibility = validated_data.get('visibility', instance.visibility)
		instance.save(update_fields=['category', 'title', 'description', 'visibility'])
		return instance

class VideoUploadSerializer(serializers.ModelSerializer):

	class Meta:
		model = Video
		fields = ['uploaded_file', 'channel', 'title', 'description', 'category', 'visibility']

	def create(self, validated_data):
		print(validated_data)
		video = Video.objects.create(channel=validated_data.get('channel'))
		video.uploaded_file = validated_data.get('uploaded_file')
		video.save()
		return video

	def update(self, instance, validated_data):
		if not validated_data.get('category', None) and not instance.category:
			raise serializers.ValidationError({'category' : 'Please select a category.'})

		instance.category = validated_data.get('category', instance.category)
		instance.description = validated_data.get('description', instance.description)
		instance.title = validated_data.get('title', instance.title)
		instance.visibility = validated_data.get('visibility', instance.visibility)
		instance.save(update_fields=['category', 'title', 'description', 'visibility'])
		return instance

	def validate_uploaded_file(self, value):
		if not magic.from_file(value.temporary_file_path(), mime=True).startswith('video/'):
		    raise serializers.ValidationError("Unsupported file type.")
		new_name = "".join(c for c in value.name if c.isalnum() or c in ['_', '-', '.'])
		value.name = new_name
		return value

class CommentSerializer(serializers.ModelSerializer):
	replies = serializers.SerializerMethodField()
	author_name = serializers.CharField(read_only=True, source='author.name')
	author_id = serializers.CharField(read_only=True, source='author.channel_id')
	likes = serializers.IntegerField(source='likes.count', required=False)
	dislikes = serializers.IntegerField(source='dislikes.count', required=False)
	text = serializers.CharField(source='sanitized_text')

	class Meta:
		model = Comment
		exclude = ['author', 'video']

	def get_replies(self, obj):
		queryset = Comment.objects.filter(parent_id=obj.id)
		serializer = CommentSerializer(queryset, many=True)
		return serializer.data

class ChannelSerializer(serializers.ModelSerializer):
	videos = serializers.CharField(source='videos.count')
	subscriptions = serializers.CharField(source='subscriptions.count')
	avatar = serializers.CharField(source='get_avatar')

	class Meta:
		model = Channel
		fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
	to_channel = ChannelSerializer()

	class Meta:
		model = Subscription
		fields = '__all__'

class GenericNotificationField(serializers.RelatedField):
	def to_representation(self, value):
		if isinstance(value, Video):
			return VideoSerializer(value).data
		if isinstance(value, Comment):
			return CommentSerializer(value).data
		if isinstance(value, Channel):
			return ChannelSerializer(value).data
		raise Exception('Unexpected type of object')

class NotificationSerializer(serializers.ModelSerializer):
	action_object = GenericNotificationField(read_only=True)
	target_object = GenericNotificationField(read_only=True)
	actor = GenericNotificationField(read_only=True)
	created = serializers.SerializerMethodField()

	def get_created(self, obj):
		return timesince(obj.created)

	class Meta:
		model = Notification
		fields = ['id', 'actor', 'action_object', 'target_object', 'created', 'notification_type', 'recipient', 'unread']
