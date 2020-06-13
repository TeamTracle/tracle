import magic

from rest_framework import serializers

from backend.models import Video

class VideoSerializer(serializers.ModelSerializer):
	created = serializers.DateTimeField(format='%c')
	thumbnail = serializers.CharField(source='get_thumbnail')
	status = serializers.CharField(source='get_video_status')

	class Meta:
		model = Video
		fields = ['pk', 'watch_id', 'title', 'created', 'thumbnail', 'views', 'likes', 'dislikes', 'visibility', 'status']

class VideoUploadSerializer(serializers.ModelSerializer):

	class Meta:
		model = Video
		fields = ['uploaded_file', 'channel', 'title', 'description', 'category']

	def create(self, validated_data):
		return Video.objects.create(**validated_data)

	def update(self, instance, validated_data):
		if not validated_data.get('category', None) and not instance.category:
			raise serializers.ValidationError({'category' : 'Please select a category.'})

		instance.category = validated_data.get('category', instance.category)
		instance.description = validated_data.get('description', instance.description)
		instance.title = validated_data.get('title', instance.title)
		instance.save(update_fields=['category', 'title', 'description'])
		return instance

	def validate_uploaded_file(self, value):
		print('value', value)
		if not magic.from_file(value.temporary_file_path(), mime=True).startswith('video/'):
		    raise serializers.ValidationError("Unsupported file type.")
		return value
