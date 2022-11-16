"""API interface for google photos."""

import json
import os

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from google_auth_oauthlib.flow import InstalledAppFlow

URL_BASE = 'https://photoslibrary.googleapis.com/'
APP_SCOPES = ['https://www.googleapis.com/auth/photoslibrary']

# https://developers.google.com/photos/library/guides/upload-media#file-types-sizes
PHOTO_TYPES = [
    'BMP', 'GIF', 'HEIC', 'ICO', 'JPG', 'PNG', 'TIFF', 'WEBP', 'RAW'
]
VIDEO_TYPES = [
    '3GP', '3G2', 'ASF', 'AVI', 'DIVX', 'M2T', 'M2TS', 'M4V',
    'MKV', 'MMV', 'MOD', 'MOV', 'MP4', 'MPG', 'MTS', 'TOD', 'WMV'
]


def valid_photo_ext(filename):
    """If file extension is acceptable photo."""
    return filename.split('.')[-1].upper() in PHOTO_TYPES


def valid_video_ext(filename):
    """If file extension is acceptable video."""
    return filename.split('.')[-1].upper() in VIDEO_TYPES


class Client(object):
    """Session scoped client object."""

    session = None

    def __init__(self, user_token_filename, app_creds_filename=None):  # noqa:E501
        """Create new authorized client.

        Args:
            user_token_filename (str): file to read/write user token
            app_creds_filename (str): file to read app config when registering user token
        """  # noqa:E501
        try:
            token = self._get_creds_from_file(user_token_filename)
        except (FileNotFoundError, json.decoder.JSONDecodeError, ValueError) as e:  # noqa:E501
            if not app_creds_filename:
                raise e
            raw_token = self._generate_auth_token(app_creds_filename)
            self._save_auth_token(raw_token, user_token_filename)
            token = self._get_creds_from_file(user_token_filename)
        self.session = AuthorizedSession(token)

    def post_batch_media(self, filenames, to_album_id, batch_size=50):
        """Upload and register batch of media items.

        Args:
            list[str]: full path filenames locally on disk
            to_album_id (str): Google Photos album id
            batch_size (int): chunk size to send files in

        Yields:
            dict: uploads results
                key (str): Google Photos upload token
                    - filename (str): full path filename uploaded
                    - media_id (str): remote id created or missing on failure
        """
        if batch_size > 50 or batch_size < 1:
            raise ValueError('Invalid batch_size')
        batches = [
            filenames[x:x + batch_size]
            for x in range(0, len(filenames), batch_size)
        ]
        for batch in batches:

            # upload bytes, record upload token by filename
            upload_tokens = {}
            for filename in batch:
                with open(filename, 'rb') as f:
                    response = self._call('POST', 'v1/uploads', data=f.read())
                    upload_tokens[response.content.decode()] = {
                        'filename': filename
                    }

            # register uploads into album
            data = json.dumps({
                'albumId': to_album_id,
                'newMediaItems': [
                    {
                        'simpleMediaItem': {
                            'uploadToken': upload_token,
                            'fileName': os.path.split(details['filename'])[-1]
                        }
                    }
                    for upload_token, details in upload_tokens.items()
                ]
            })
            response = self._call('POST', 'v1/mediaItems:batchCreate', data=data)  # noqa:E501

            # record sucess
            for result in response.json()['newMediaItemResults']:
                if result['status']['message'] == 'Success':
                    upload_tokens[result['uploadToken']]['media_id'] = result['mediaItem']['id']  # noqa:E501

            # yield batch to be processed
            yield upload_tokens

    def list_albums(self, exclude_non_app=True, page_size=50):
        """View all albums user has access to.

        Args:
            exclude_non_app (bool): don't show albums not created by this app
            page_size (int): batch size to fetch

        Returns:
            list[Album]: https://developers.google.com/photos/library/reference/rest/v1/albums#Album
        """  # noqa:E501
        if page_size > 50 or page_size < 1:
            raise ValueError('Invalid page_size')
        params = {
            'pageSize': page_size,
            'excludeNonAppCreatedData': exclude_non_app
        }
        results = []
        while True:
            response = self._call('GET', 'v1/albums', params=params)
            data = response.json()
            albums_batch = data.get('albums', [])
            results += albums_batch
            if len(albums_batch) < page_size:
                break
            params['pageToken'] = data['nextPageToken']
        return results

    def create_album(self, title):
        """Make new album.

        Args:
            title (str): human readable name of album

        Returns:
            Album: https://developers.google.com/photos/library/reference/rest/v1/albums#Album
        """  # noqa:E501
        data = json.dumps({
            'album': {
                'title': title
            }
        })
        return self._call('POST', 'v1/albums', data=data)

    def _call(self, verb, url, **kwargs):
        response = self.session.request(
            verb,
            URL_BASE + url,
            **kwargs
        )
        status_code = response.status_code
        if status_code < 200 or status_code > 300:
            raise Exception(f'Unexpected HTTP code "{status_code}" @ "{verb} {url}"')  # noqa:E501
        return response

    def _save_auth_token(self, token, filename):
        data = {
            prop: getattr(token, prop)
            for prop in [
                'token',
                'refresh_token',
                'scopes',
                'token_uri',
                'client_id',
                'client_secret'
            ]
        }
        with open(filename, 'w') as f:
            f.write(json.dumps(data))

    def _generate_auth_token(self, filename):
        flow = InstalledAppFlow.from_client_secrets_file(
            filename,
            scopes=APP_SCOPES
        )
        return flow.run_local_server()

    def _get_creds_from_file(self, filename):
        return Credentials.from_authorized_user_file(
                filename,
                APP_SCOPES
        )
