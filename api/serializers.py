from rest_framework import serializers

from backend.models import Video

class VideoSerializer(serializers.ModelSerializer):
	created = serializers.DateTimeField(format='%c')
	class Meta:
		model = Video
		fields = ['pk', 'watch_id', 'title', 'created', 'views', 'thumbnail', 'likes', 'dislikes', 'visibility']