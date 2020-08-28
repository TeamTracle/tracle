import magic

from rest_framework import serializers

from backend.models import Video

class VideoSerializer(serializers.ModelSerializer):
	created = serializers.DateTimeField(format='%c')
	thumbnail = serializers.CharField(source='get_thumbnail')
	# status = serializers.CharField(source='get_video_status')

	class Meta:
		model = Video
		fields = ['pk', 'watch_id', 'title', 'description', 'thumbnail', 'created', 'views', 'likes', 'dislikes', 'visibility', 'transcode_status', 'published']


class VideoEditSerializer(serializers.ModelSerializer):
	class Meta:
		model = Video
		fields = ['title', 'description', 'category']

	def update(self, instance, validated_data):
		instance.category = validated_data.get('category', instance.category)
		instance.description = validated_data.get('description', instance.description)
		instance.title = validated_data.get('title', instance.title)
		instance.save(update_fields=['category', 'title', 'description'])
		return instance

class VideoUploadSerializer(serializers.ModelSerializer):

	class Meta:
		model = Video
		fields = ['uploaded_file', 'channel', 'title', 'description', 'category']

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
		instance.save(update_fields=['category', 'title', 'description'])
		return instance

	def validate_uploaded_file(self, value):
		if not magic.from_file(value.temporary_file_path(), mime=True).startswith('video/'):
		    raise serializers.ValidationError("Unsupported file type.")
		new_name = "".join(c for c in value.name if c.isalnum() or c in ['_', '-', '.'])
		value.name = new_name
		return value
