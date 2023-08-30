"""CLI to upload to google-photos."""

import argparse
import os

from database import DB

from gphoto import Client
from gphoto import valid_photo_ext
from gphoto import valid_video_ext

from tabulate import tabulate


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    """Entrypoint."""
    default_app_data_filename = os.path.join(SCRIPT_DIR, 'database/.app_data')
    default_token_filename = os.path.join(SCRIPT_DIR, 'auth_token.json')
    default_credentials_filename = os.path.join(SCRIPT_DIR, 'credentials.json')

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--app-data',
        default=default_app_data_filename,
        help='filename to store app data in sqlite'
    )

    subparser = parser.add_subparsers(dest='command')

    create_auth_subparser = subparser.add_parser(
        'create-auth',
        help='retrieve valid auth token',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    create_auth_subparser.add_argument(
        '--token-file',
        default=default_token_filename,
        help='filename for oauth user token'
    )
    create_auth_subparser.add_argument(
        '--creds-file',
        default=default_credentials_filename,
        help='application creds used to get user token'
    )
    create_auth_subparser.set_defaults(func=create_auth)

    list_albums_subparser = subparser.add_parser(
        'list-albums',
        help='list locally registred albums, and optionally all remote ones',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    list_albums_subparser.add_argument(
        '-a',
        action='store_true',
        help='include remote albums'
    )
    list_albums_subparser.add_argument(
        '--token-file',
        default=default_token_filename,
        help='filename for oauth user token, only relevent if -a is set'
    )
    list_albums_subparser.set_defaults(func=list_albums)

    create_album_subparser = subparser.add_parser(
        'create-album',
        help='make new album in cloud and register locally',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    create_album_subparser.add_argument(
        'name',
        help='name for new album'
    )
    create_album_subparser.add_argument(
        '--token-file',
        default=default_token_filename,
        help='filename for oauth user token'
    )
    create_album_subparser.set_defaults(func=create_album)

    upload_album_subparser = subparser.add_parser(
        'upload-album',
        help='upload new content from local dir to cloud album',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    upload_album_subparser.add_argument(
        'from_dir',
        help='local folder to upload to gphotos'
    )
    upload_album_subparser.add_argument(
        'to_album',
        type=int,
        help='id of albumn in db to upload into'
    )
    upload_album_subparser.add_argument(
        '--token-file',
        default=default_token_filename,
        help='filename for oauth user token'
    )
    upload_album_subparser.add_argument(
        '-e',
        action='store_true',
        help='exit non-zero if any uploads in batch failed'
    )
    upload_album_subparser.add_argument(
        '-s',
        action='store_true',
        help='exit non-zero if invalid file found in dir'
    )
    upload_album_subparser.set_defaults(func=upload_album)

    # parse and save args
    args = parser.parse_args()

    # call func related to command
    if 'func' not in args:
        parser.print_help()
        exit(1)

    db = DB(args.app_data)

    args.func(args, db)


def create_auth(args, db):
    """Create user auth token via OAuth browser flow."""
    token_file = args.token_file
    creds_file = args.creds_file
    Client(token_file, creds_file)
    print(f'Created token file at "{token_file}"')


def list_albums(args, db):
    """Display all locally registered albums."""
    include_remote = args.a
    token_filename = args.token_file

    # query db for local albums
    local_albums = db.select_albums()

    if include_remote:

        # query for remote albums
        client = Client(token_filename)
        remote_albums = {
            x['id']: x
            for x in client.list_albums(exclude_non_app=False)
        }
        if remote_albums and not local_albums:
            print('No albums found locally or remote!')
            exit(0)

        # format data for display
        headers = ['id', 'gid', 'local name', 'remote name']
        rows = []

        # locally registered albums, enriched with remote data
        for local in local_albums:
            remote_name = remote_albums.get(local['gid'], {}).get('title', None)  # noqa:E501
            rows.append(list(local) + [remote_name])
            if local['gid'] in remote_albums:
                del remote_albums[local['gid']]

        # albums not registered locally
        for _, remote in remote_albums.items():
            rows.append([
                None,
                remote['id'],
                None,
                remote['title']
            ])
    else:
        if not local_albums:
            print('No albums registered locally')
            exit(0)

        # format data for display
        headers = local_albums[0].keys()
        rows = local_albums

    print(tabulate(
        rows,
        headers=headers,
        tablefmt='pretty'
    ))


def create_album(args, db):
    """Create remote album and register it locally."""
    album_name = args.name
    token_filename = args.token_file

    client = Client(token_filename)
    response = client.create_album(album_name).json()
    print(f'Created album "{album_name}" in cloud')

    db.insert_album(response['id'], response['title'])
    print('Added album in db!')


def upload_album(args, db):
    """Upload all files in a directory into a remote album."""
    album_id = args.to_album
    local_dir = os.path.abspath(args.from_dir)
    token_filename = args.token_file
    exit_on_error = args.e
    exit_on_invalid_file = args.s

    # validate input album and get gid
    album = db.select_album(album_id)
    if not album:
        print(f'Album not found for id "{album_id}"')
        exit(1)
    album_gid = album['gid']

    # validate directory exists
    try:
        filenames = os.listdir(local_dir)
    except FileNotFoundError:
        print(f'Local dir not found at "{local_dir}"')
        exit(1)

    # list files and filter based on extension
    num_total_files = len(filenames)
    filenames = [
        x
        for x in filenames
        if valid_photo_ext(x) or valid_video_ext(x)
    ]
    if exit_on_invalid_file and num_total_files != len(filenames):
        print('Invalid files found in upload dir')
        exit(1)
    if not filenames:
        print('No valid files found to upload!')
        exit(0)

    # get files in dir already uploaded
    uploaded = db.select_uploads(
        local_dir,
        album_id
    )
    uploaded_files = [
        x['filename']
        for x in uploaded
    ]
    filenames = [
        x
        for x in filenames
        if x not in uploaded_files
    ]
    if not filenames:
        print('No pending files found to upload!')
        exit(0)

    # upload files to album, saving results one batch at a time
    client = Client(token_filename)
    for upload_results in client.post_batch_media(
        [
            os.path.join(local_dir, x)
            for x in filenames
        ],
        album_gid
    ):

        # process batch results from API
        batch = [
            {
                'album_id': album_id,
                'local_dir': local_dir,
                'filename': os.path.split(x['filename'])[-1],
                'media_id': x.get('media_id')
            }
            for _, x in upload_results.items()
        ]
        db.insert_uploads(batch)

        # progress report
        for x in batch:
            print(f"{x['filename']} => {x['media_id']}")

        # stop if upload errors occured
        if exit_on_error and any([y['media_id'] is None for y in batch]):
            exit(1)


if __name__ == '__main__':
    main()
