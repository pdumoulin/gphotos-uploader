# exif notes

Time zone aware date [exif image tags](https://exiv2.org/tags.html) are interpreted by Google Photos, but not documented. These are my notes on figuring out what tags to set and how to set them using python to benefit [this project](https://github.com/pdumoulin/brightwheel-downloader).

:warning: Google photos on Android **does not** respect time zone when displaying images in a unified feed, but on the Web version it does!

:heavy_exclamation_mark: All experiments were run on jpg files only.


### Discover Tags

Using [exiftool](https://exiftool.org/) and a photo taken with an Android phone, I removed tags and uploaded the result to Google Photos until the datetime and timezone were no longer displayed as expected.

Here are the minimum necessary tags needed.

| code | exiftool name | reference name | example |
| --- | --- |--- | --- |
| 306 | ModifyDate | Exif.Image.DateTime | `2021:07:12 12:03:24` |
| 36882  | OffsetTimeDigitized | Exif.Photo.OffsetTimeDigitized | `+07:00` |


### Set via Python

Depending on how these tags were set via a python script, Google Photos would not recognize them.

See `run.py` to experiment with each method.

| method | date works | time zone works |
| --- | --- | --- |
| [Pillow](https://pypi.org/project/Pillow/) | yes | no |
| [PyExifTool](https://pypi.org/project/PyExifTool/) | no | no |
| exiftool via [subprocess](https://docs.python.org/3/library/subprocess.html) | yes | yes |

Examining tags using exiftool only shows tag ordering as different for each method. After many attempts, the only consistent way to set both datetime and time zone is calling exiftool directly.
