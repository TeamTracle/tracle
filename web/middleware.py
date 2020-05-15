from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from backend.queries import get_channel


class SelectedChannelMiddleware(MiddlewareMixin):

	def process_request(self, request):
		if request.user.is_authenticated:
			print('USER IS AUTHENTICATED')
			channel = get_channel(request.user)
			request.channel = channel
			print(request.channel)
		else:
			print('ANONYMOUS USER')
