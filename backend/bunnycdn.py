import urllib3, requests

from django.conf import settings

def upload_file(local_file, remote_path):
	payload = None
	with open(local_file, 'rb') as f:
		payload = f.read()

	if payload:
		token = settings.BUNNYCDN['token']
		url = '{}/{}'.format(settings.BUNNYCDN['base_url'], remote_path)
		headers = {
			'AccessKey' : token,
			'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
			'Content-Length' : str(len(payload))
 			}
		r = requests.put(
			url,
			headers=headers,
			data=payload)
		print(r.text)

	else:
		print('No Payload???')

def delete_file(remote_path):
	token = settings.BUNNYCDN['token']
	url = '{}/{}'.format(settings.BUNNYCDN['base_url'], remote_path)
	print(url)
	r = requests.delete(
		url,
		headers={'AccessKey' : token})
	print(r.text)
