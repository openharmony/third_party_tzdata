#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import time
import urllib.request as request
import urllib.error as error
import ssl
import tarfile
import sys
import os
import stat


def find_current_version(path):
    flags = os.O_RDONLY
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(path, flags, modes), 'r') as file:
        version = file.readline().strip()
        return version


def try_download(file_type, try_version, save_path, version):
    if try_version == version:
        print('current version is already the lastest version.')
        return 0
    parent_url = "https://data.iana.org/time-zones/releases/"
    context = ssl.SSLContext()
    try:
        file_name = file_type + try_version + '.tar.gz'
        data = request.urlopen(parent_url + file_name, context=context)
    except error.HTTPError as http_error:
        return -1
    print('start to download ' + file_name)
    content = data.read()
    data.close()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(save_path + file_name, flags, modes), 'wb+') as file:
        file.write(content)
    print('download finished!')
    return 1


def download(file_type, save_path, version):
    local_time = time.localtime(time.time())
    year = local_time[0]
    version_suffixes = "zyxwvutsrqponmlkjihgfedcba"
    version_index = 0

    print('start to find the lastest version of tzdata and tzcode.')
    status = -1
    while status < 0:
        status = try_download(file_type, str(year) +
                              version_suffixes[version_index], save_path,
                              version)
        if status < 0:
            if version_index < 25:
                version_index += 1
            else:
                year -= 1
                version_index = 0
    if status == 0:
        return ''
    file_name = file_type + str(year) + version_suffixes[version_index] + \
                '.tar.gz'
    return file_name


def decompress(file_name, save_path):
    tar = tarfile.open(save_path + file_name, "r:gz")
    tar.extractall(save_path)
    tar.close()
    print('decompress finished!')


def main():
    file_path = os.path.abspath(__file__)
    file_dir = os.path.dirname(file_path)

    version_file_path = file_dir + "/../../data/prebuild/posix/version.txt"
    version = find_current_version(version_file_path)

    print('current version is ' + version)

    download_path = file_dir + "/../../data/iana/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    file_type = "tzdata"
    file_name = download(file_type, download_path, version)

    if file_name != '':
        decompress(file_name, download_path)
        file_type = "tzcode"
        new_version = file_name[6:11]
        try_download(file_type, new_version, download_path, version)
        decompress(file_type + new_version + '.tar.gz', download_path)
        flags = os.O_WRONLY | os.O_CREAT
        modes = stat.S_IWUSR | stat.S_IRUSR
        with os.fdopen(os.open(os.path.join(download_path, 'version.txt'), flags, modes), 'w') as file:
            file.write(new_version + '\n')


if __name__ == '__main__':
    sys.exit(main())
