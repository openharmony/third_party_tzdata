#!/bin/bash
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
set -e
script_path=$(cd $(dirname $0);pwd)
iana_path="${script_path}/../../data/iana"
posix_path="${iana_path}/../prebuild/posix"
zic_path="${iana_path}/../prebuild/tool/linux"

while getopts "o:b" arg;
do
    case "${arg}" in
        "o")
            tool_bin_dir=${OPTARG}
        ;;
        ?)
          echo "unkonw argument"
          exit 1
        ;;
    esac
done
echo "tool_bin_dir--@@:"${tool_bin_dir}
make -C ${iana_path}
mkdir -p ${zic_path}
mkdir -p ${posix_path}
mv ${iana_path}/zic ${zic_path}

state_name=('africa' 'antarctica' 'asia' 'australasia' 'europe' 'etcetera' 'northamerica' 'southamerica' 'backward')
for name in ${state_name[@]}
do
    ${zic_path}/zic -d ${iana_path}/zoneinfo ${iana_path}/$name
done

rm -rf ${posix_path}/*
mv ${iana_path}/zoneinfo/* ${posix_path}
#mv ${iana_path}/version.txt ${posix_path}
output_path=${script_path}/../../../../${tool_bin_dir}/thirdparty/tzdata/output
echo ${output_path}
mkdir "${script_path}/../../data/prebuild/posix/output"
echo 'compile done'
python3 ${script_path}/zone_compactor.py "${script_path}/../../data/prebuild/normal/timezone_list.cfg" ${posix_path} "${output_path}" "tzdata2026b"
echo 'package done'
exit 0