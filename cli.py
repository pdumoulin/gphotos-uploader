"""CLI to upload to google-photos."""

import argparse
import os

from database import DB

from gphoto import Client

from tabulate import tabulate


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    """Entrypoint."""
    default_app_data_filename = os.path.join(SCRIPT_DIR, 'database/.app_data')

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
        default='auth_token.json',
        help='filename for oauth user token'
    )
    create_auth_subparser.add_argument(
        '--creds-file',
        default='credentials.json',
        help='application creds used to get user token'
    )
    create_auth_subparser.set_defaults(func=create_auth)

    list_albums_subparser = subparser.add_parser(
        'list-albums',
        help='list locally registred albums',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
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
        default='auth_token.json',
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
        default='auth_token.json',
        help='filename for oauth user token'
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
    token_file = args.token_file
    creds_file = args.creds_file
    Client(token_file, creds_file)
    print(f'Created token file at "{token_file}"')

def list_albums(args, db):
    rows = db.select_albums()
    if rows:
        print(tabulate(
            rows,
            headers=rows[0].keys(),
            tablefmt='pretty'
        ))

def create_album(args, db):
    print(args)
    album_name = args.name
    token_filename = args.token_file

    client = Client(token_filename)
    response = client.create_album(album_name).json()
    print(f'Created album "{album_name}" in cloud')

    db.insert_album(response['id'], response['title'])
    print('Added album in db!')

def upload_album(args, db):
    album_id = args.to_album
    local_dir = os.path.abspath(args.from_dir)
    token_filename = args.token_file

    # validate input album and get gid
    rows = db.select_album(album_id)
    if not rows:
        print(f'Album not found for id "{album_id}"')
        exit(1)
    album_gid = rows[0]['gid']

    # validate directory exists
    try:
        filenames = os.listdir(local_dir)
    except FileNotFoundError:
        print(f'Local dir not found at "{local_dir}"')
        exit(1)

    # list files and filter based on extension
    # https://developers.google.com/photos/library/guides/upload-media
    extensions = [
        'BMP', 'GIF', 'HEIC', 'ICO', 'JPG', 'PNG', 'TIFF', 'WEBP',
        '3GP', '3G2', 'ASF', 'AVI', 'DIVX', 'M2T', 'M2TS', 'M4V',
        'MKV', 'MMV', 'MOD', 'MOV', 'MP4', 'MPG', 'MTS', 'TOD', 'WMV'
    ]
    filenames = [
        x
        for x in filenames
        if x.split('.')[-1].upper() in extensions
    ]
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
            if x.split('.')[-1].upper() in extensions
        ],
        album_gid
    ):
        uploads = [
                {
                    'album_id': album_id,
                    'local_dir': local_dir,
                    'filename': os.path.split(x['filename'])[-1],
                    'success': x['success']
                }
                for _, x in upload_results.items()
            ]
        db.insert_uploads(uploads)
        for upload in uploads:
            print(f"{upload['filename']} => {upload['success']}")


if __name__ == '__main__':
    main()
