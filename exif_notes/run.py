"""Test setting Google Photos compatible time tags."""

import shlex
import subprocess
import sys

from PIL import Image

from exiftool import ExifTool


def main():
    """Entrypoint."""
    mode = sys.argv[1].lower()
    filename = sys.argv[2]

    # datetime tag
    date_code = 306
    date_name = 'ModifyDate'
    date_value = '2021:11:11 12:03:00'

    # time zone tag
    tz_code = 36882
    tz_name = 'OffsetTimeDigitized'
    tz_value = '+07:00'

    # Datetime - yes ; Offset - no
    if mode == 'pillow':
        im = Image.open(filename)
        exif = im.getexif()
        exif.update(
            [
                (date_code, date_value),
                (tz_code, tz_value)
            ]
        )
        im.save(filename, exif=exif, quality=100)

    # Datetime - no ; Offset - no
    elif mode == 'pyexiftool':
        with ExifTool() as et:
            et.execute(
                f"-{date_name}='{date_value}'",
                filename
            )
            et.execute(
                f"-{tz_name}='{tz_value}'",
                filename
            )

    # Datetime - yes ; Offset - yes
    elif mode == 'subprocess':
        date_command = shlex.split(f"exiftool -{date_name}='{date_value}' {filename}")  # noqa:E501
        subprocess.run(
            date_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=True
        )

        tz_command = shlex.split(f"exiftool -{tz_name}='{tz_value}' {filename}")  # noqa:E501
        subprocess.run(
            tz_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=True
        )
    else:
        raise Exception(f'mode {mode} bad')


if __name__ == '__main__':
    main()
