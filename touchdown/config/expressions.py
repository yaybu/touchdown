# Copyright 2016 Isotoma Limited
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

import random
import string

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dsa, rsa

from touchdown.core import serializers
from touchdown.core.utils import force_str

DJANGO_SECRET_KEY_SYMBOLS = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'

__all__ = [
    'pwgen',
    'django_secret_key',
    'fernet_secret_key',
    'rsa_private_key',
    'dsa_private_key',
]


def expression(wraps):
    def fn(*args, **kwargs):
        return serializers.Expression(
            lambda r, o: wraps(*args, **kwargs)
        )
    return fn


@expression
def pwgen(length=28, lower=True, upper=True, numeric=True, symbols=False):
    system_random = random.SystemRandom()
    sym = []
    if lower:
        sym.extend(string.ascii_lowercase)
    if upper:
        sym.extend(string.ascii_uppercase)
    if numeric:
        sym.extend(string.digits)
    if symbols:
        sym.extend(string.punctuation)
    return ''.join([
        system_random.choice(sym) for i in range(length)
    ])


@expression
def django_secret_key():
    system_random = random.SystemRandom()
    return ''.join([
        system_random.choice(DJANGO_SECRET_KEY_SYMBOLS) for i in range(50)
    ])


@expression
def fernet_secret_key():
    return Fernet.generate_key()


@expression
def rsa_private_key():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    return force_str(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))


@expression
def dsa_private_key():
    private_key = force_str(dsa.generate_private_key(
        key_size=1024,
        backend=default_backend()
    ))
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
