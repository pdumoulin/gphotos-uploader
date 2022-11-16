"""Docstring."""

# https://exiv2.org/tags.html

import argparse
import pprint

from PIL import ExifTags
from PIL import Image


def main():
    """Entrypoint."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'filename',
        help='name of file to process'
    )

    subparser = parser.add_subparsers(dest='command')

    read_subparser = subparser.add_parser(
        'read',
        help='display existing exif data'
    )
    read_subparser.set_defaults(func=read)

    write_subparser = subparser.add_parser(
        'write',
        help='edit exif data'
    )
    write_subparser.add_argument(
        'code',
        type=int,
        help='exif code to write into'
    )
    write_subparser.add_argument(
        'value',
        type=str,
        help='exif data to write'
    )
    write_subparser.set_defaults(func=write)

    clear_subparser = subparser.add_parser(
        'clear',
        help='remove all exif data'
    )
    clear_subparser.set_defaults(func=clear)

    args = parser.parse_args()
    if 'func' not in args:
        parser.print_help()
        exit(1)
    args.func(args)


def clear(args):
    """Delete exif data from file."""
    filename = args.filename
    im = Image.open(filename)
    im.save(filename, exif=b'')


def write(args):
    """Save exif data to file."""
    filename = args.filename
    code = args.code
    value = args.value
    im = Image.open(filename)
    exif = im.getexif()
    exif.update([
        (code, value)
    ])
    im.save(filename, exif=exif)


def read(args):
    """Pprint exif data from file."""
    filename = args.filename
    tag_table = {}
    tag_table.update(ExifTags.TAGS)
    tag_table.update(ExifTags.GPSTAGS)
    im = Image.open(filename)
    exif = im.getexif()
    tags = {
        k: {
            tag_table[k]: v
        }
        for k, v in exif.items()
        if k in tag_table
    }
    pprint.pprint(tags, indent=4)

    # TODO - can this data be set and read by GooglePhotos?
    gps_info = exif.get_ifd(34853)
    pprint.pprint(gps_info)


if __name__ == '__main__':
    main()
