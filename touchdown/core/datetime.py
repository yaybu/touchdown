# Copyright 2011-2015 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import re
import time
from datetime import datetime, timedelta, tzinfo

from touchdown.core import errors

try:
    import pytz
except ImportError:
    pytz = None

try:
    from dateutil import parser
except ImportError:
    parser = None


REGEX_DELTA = re.compile(
    r'(\d+)\s?(m|minute|minutes|h|hour|hours|d|day|days|w|weeks|weeks)(?: ago)?'
)

UNITS = {
    'm': 60,
    'h': 60 * 60,
    'd': 60 * 60 * 24,
    'w': 60 * 60 * 24 * 7,
}

if not pytz:
    class UTC(tzinfo):

        def __repr__(self):
            return '<UTC>'

        def utcoffset(self, value):
            return timedelta(0)

        def tzname(self, value):
            return 'UTC'

        def dst(self, value):
            return timedelta(0)

        def localize(self, value):
            value.replace(tzinfo=self)

    utc = UTC()
else:
    utc = pytz.utc

_EPOCH = datetime(1970, 1, 1, tzinfo=utc)


def now():
    return datetime.utcnow().replace(tzinfo=utc)


def parse_datetime(value):
    match = REGEX_DELTA.match(value)
    if match:
        amount, unit = match.groups()
        return now() - timedelta(
            seconds=int(amount) * UNITS[unit[0]],
        )

    if parser:
        try:
            return parser.parse(value)
        except Exception:
            raise errors.Error(
                'Unable to parse {} as a date or time'.format(value)
            )

    raise errors.Error(
        'Unable to parse {} as a date or time'.format(value)
    )


def as_seconds(value):
    if value.tzinfo is None:
        return int(time.mktime((
            value.year, value.month, value.day,
            value.hour, value.minute, value.second,
            -1, -1, -1)))
    else:
        return int((value - _EPOCH).total_seconds())
