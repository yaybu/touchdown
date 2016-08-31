# Copyright 2015 Isotoma Limited
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

import json
import os
import string

from touchdown.core import errors


class Cache(object):

    def __contains__(self, cache_key):
        raise NotImplementedError(self.__contains__)

    def __getitem__(self, cache_key):
        raise NotImplementedError(self.__getitem__)

    def __setitem__(self, cache_key, value):
        raise NotImplementedError(self.__setitem__)


class FileCache(Cache):

    extension = ''

    def __init__(self, cache_directory):
        self.cache_directory = cache_directory

    def _ensure_cache_directory_exists(self):
        if not os.path.isdir(self.cache_directory):
            os.makedirs(self.cache_directory)

    def _cache_key_to_path(self, cache_key):
        valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
        cache_key = ''.join(c for c in cache_key if c in valid_chars)
        cache_key = cache_key.replace(' ', '_')
        return os.path.join(self.cache_directory, cache_key + self.extension)

    def _serialize(self, contents):
        raise NotImplementedError(self._serialize)

    def _deserialize(self, contents):
        raise NotImplementedError(self._deserialize)

    def __contains__(self, cache_key):
        return os.path.isfile(self._cache_key_to_path(cache_key))

    def __getitem__(self, cache_key):
        path = self._cache_key_to_path(cache_key)
        with open(path, 'r') as fp:
            return self._deserialize(fp.read())

    def __setitem__(self, cache_key, value):
        path = self._cache_key_to_path(cache_key)
        contents = self._serialize(value)

        self._ensure_cache_directory_exists()

        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(contents)


class JSONFileCache(FileCache):

    extension = '.json'

    def _serialize(self, contents):
        try:
            return json.dumps(contents)
        except (TypeError, ValueError):
            raise errors.Error('\'%s\' cannot be serialised' % contents)

    def _deserialize(self, contents):
        try:
            return json.loads(contents)
        except (ValueError,):
            raise errors.Error('\'%s\' cannot be deserialised' % contents)
