# Copyright (c) 2025 Huawei Device Co., Ltd.
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

"""
usage: python zone_compactor.py <setup file> <data directory> <output directory> <tzdata version>

Compile a set of tzfile-formatted files into a single file containing an index.

The compilation is controlled by a setup file, which is provided as a
command-line argument.  The setup file has the form:

Link <toName> <fromName>

<zone filename>


Note that the links must be declared prior to the zone names.
A zone name is a filename relative to the source directory such as
'GMT', 'Africa/Dakar', or 'America/Argentina/Jujuy'.

Use the 'zic' command-line tool to convert from flat files
(such as 'africa' or 'northamerica') to a directory
hierarchy suitable for this tool (containing files such as 'data/Africa/Abidjan').

@since 2025/02/08
"""

import os
import struct
import sys
from collections import OrderedDict

MAXNAME = 40


class ZoneCompactor:

    def __init__(self, setup_file, data_directory, output_directory, version):
        zone_ids = []
        seen = set()
        with open(setup_file, 'r') as reader:
            for line in reader:
                s = line.strip()
                if s and s not in seen:
                    seen.add(s)
                    zone_ids.append(s)

        all_data = bytearray()
        offset = 0
        offsets = {}
        lengths = {}
        for zone_id in zone_ids:
            source_file = os.path.join(data_directory, zone_id)
            length = os.path.getsize(source_file)
            offsets[zone_id] = offset
            lengths[zone_id] = length
            offset += length
            with open(source_file, 'rb') as f:
                all_data.extend(f.read())

        os.makedirs(output_directory, exist_ok=True)
        output_path = os.path.join(output_directory, "tzdata")
        with open(output_path, 'wb') as f:
            f.write(self._to_ascii(bytearray(12), version))

            index_offset_offset = f.tell()
            f.write(struct.pack('>i', 0))
            data_offset_offset = f.tell()
            f.write(struct.pack('>i', 0))
            final_offset_offset = f.tell()
            f.write(struct.pack('>i', 0))

            index_offset = f.tell()
            sorted_olson_ids = sorted(offsets.keys())
            for zone_name in sorted_olson_ids:
                if len(zone_name) >= MAXNAME:
                    raise RuntimeError(f"zone filename too long: {len(zone_name)}")
                f.write(self._to_ascii(bytearray(MAXNAME), zone_name))
                f.write(struct.pack('>i', offsets[zone_name]))
                f.write(struct.pack('>i', lengths[zone_name]))

            data_offset = f.tell()
            f.write(all_data)
            final_offset = f.tell()

            f.seek(index_offset_offset)
            f.write(struct.pack('>i', index_offset))
            f.seek(data_offset_offset)
            f.write(struct.pack('>i', data_offset))
            f.seek(final_offset_offset)
            f.write(struct.pack('>i', final_offset))

    @staticmethod
    def _to_ascii(dst, src):
        for i in range(len(src)):
            if ord(src[i]) > ord('~'):
                raise RuntimeError(f"non-ASCII string: {src}")
            dst[i] = ord(src[i])
        return dst


def deep(f, stack, last, result_list):
    if os.path.isdir(f):
        stack.append(os.path.basename(f))
        files = os.listdir(f)
        for i, file in enumerate(files):
            deep(os.path.join(f, file), stack, i == len(files) - 1, result_list)
    else:
        if not stack:
            name = os.path.basename(f)
            if name not in result_list and '.' not in name:
                result_list.append(name)
        else:
            str_path = '/'.join(stack)
            full_path = str_path + '/' + os.path.basename(f)
            if full_path not in result_list:
                result_list.append(full_path)
            if last:
                stack.pop()


def main():
    setup_file_path = r"C:\Users\Administrator\Desktop\iana\setup"
    data_dir = r"C:\Users\Administrator\Desktop\iana\tzdata2026b\posix"
    output_dir = r"C:\Users\Administrator\Desktop\iana\tzdata2026b\output"
    tzdata_version = "tzdata2026b"
    ZoneCompactor(setup_file_path, data_dir, output_dir, tzdata_version)


if __name__ == '__main__':
    if len(sys.argv) == 5:
        ZoneCompactor(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        main()
