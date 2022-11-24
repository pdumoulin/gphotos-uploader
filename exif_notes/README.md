# exif notes

Time zone aware date [exif tags](https://exiv2.org/tags.html) are interpreted by Google Photos, but not documented. These are my notes on figuring out what tags to set and how to set them using python to benefit [this project](https://github.com/pdumoulin/brightwheel-downloader).

:heavy_exclamation_mark: All experiments were run on jpg and mp4 files only.


## Discover Tags

Using [exiftool](https://exiftool.org/) and a media taken with an Android phone, I removed tags and uploaded the result to Google Photos until the datetime and timezone were no longer displayed as expected.

#### Image Datetime

Google Photos on Android does not respect time zone offset, but the web version does. In order to have a consistent image feed, be sure to set `ModifyDate` to the local time zone of most photos in your feed.

| exiftool tag name | example |
| --- | --- |
| ModifyDate | `2021:07:12 12:03:24` |
| OffsetTimeDigitized | `+07:00` |

#### Image GPS

| exiftool tag name | example |
| --- | --- |
| gpslatitude | `40.678177` |
| gpslongitude | `-73.944160` |
| gpslatituderef | `N` |
| gpslongituderef | `W`|

#### Video Datetime

Google Photos uses GPS data to localize date by time zone.

| exiftool tag name | example |
| --- | --- |
|ModifyDate| `2021:07:12 12:03:24` |
| GPSCoordinates | `40.6781, 73.9441, 0` |

:warning: More than 4 decimal places may not work!

## Set via Python

Depending on how these tags were set via a python script, Google Photos would not recognize them.

See `run.py` to experiment with each method.

| method | date works | time zone works |
| --- | --- | --- |
| [Pillow](https://pypi.org/project/Pillow/) | yes | no |
| [PyExifTool](https://pypi.org/project/PyExifTool/) | no | no |
| exiftool via [subprocess](https://docs.python.org/3/library/subprocess.html) | yes | yes |

Examining tags using exiftool only shows tag ordering as different for each method. After many attempts, the only consistent way to set both datetime and time zone is calling exiftool directly.
