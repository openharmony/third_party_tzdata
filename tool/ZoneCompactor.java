/*
 * Copyright (c) 2025 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.oh.tzdata.tools;

import java.io.InputStream;
import java.io.BufferedReader;
import java.io.RandomAccessFile;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.OutputStream;
import java.util.Collections;
import java.util.Map;
import java.util.HashMap;
import java.util.Set;
import java.util.LinkedHashSet;
import java.util.ArrayList;

/**
 * usage: java ZoneCompactor <setup file> <data directory> <output directory> <tzdata version>
 *
 * Compile a set of tzfile-formatted files into a single file containing an index.
 *
 * The compilation is controlled by a setup file, which is provided as a
 * command-line argument.  The setup file has the form:
 *
 * Link <toName> <fromName>
 *
 * <zone filename>
 *
 *
 * Note that the links must be declared prior to the zone names.
 * A zone name is a filename relative to the source directory such as
 * 'GMT', 'Africa/Dakar', or 'America/Argentina/Jujuy'.
 *
 * Use the 'zic' command-line tool to convert from flat files
 * (such as 'africa' or 'northamerica') to a directory
 * hierarchy suitable for this tool (containing files such as 'data/Africa/Abidjan').
 *
 * @since 2025/02/08
 */
public class ZoneCompactor {
    // Maximum number of characters in a zone name, including '\0' terminator.
    private static final int MAXNAME = 40;

    private static final String READ_WRITE_MODE = "rw";

    // Zone name synonyms.
    private Map<String, String> links = new HashMap<>();

    // File offsets by zone name.
    private Map<String, Integer> offsets = new HashMap<>();

    // File lengths by zone name.
    private Map<String, Integer> lengths = new HashMap<>();

    /**
     * Main method to compact timezone data file
     *
     * @param setupFile timezone list file
     * @param dataDirectory timezone binary file directory
     * @param outputDirectory generate tzdata file directory
     * @param version tzdata version eg:"tzdata2025a"
     * @throws Exception input param invalid
     */
    public ZoneCompactor(String setupFile, String dataDirectory, String outputDirectory,
        String version) throws Exception {
        // Read the setup file and concatenate all the data.
        Set<String> zoneIds = new LinkedHashSet<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(setupFile))) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                zoneIds.add(line);
            }
        }

        ByteArrayOutputStream allData = new ByteArrayOutputStream();
        int offset = 0;
        for (String zoneId : zoneIds) {
            File sourceFile = new File(dataDirectory, zoneId);
            long length = sourceFile.length();
            offsets.put(zoneId, offset);
            lengths.put(zoneId, (int) length);
            offset += length;
            copyFile(sourceFile, allData);
        }
        writeFile(outputDirectory, version, allData);
    }

    /**
     * Write tzdata file
     *
     * @param outputDirectory generate tzdata file directory
     * @param version tzdata version eg:"tzdata2025a"
     * @param allData temp file
     * @throws Exception input param invalid
     */
    private void writeFile(String outputDirectory, String version,
                           ByteArrayOutputStream allData) throws Exception {
        // Create/truncate the destination file.
        try (RandomAccessFile f = new RandomAccessFile(new File(outputDirectory, "tzdata"), READ_WRITE_MODE)) {
            f.setLength(0);
            // tzdata_version
            f.write(toAscii(new byte[12], version));
            // Write placeholder values for the offsets, and remember where we need to seek back to later
            // when we have the real values.
            int indexOffsetOffset = (int) f.getFilePointer();
            f.writeInt(0);
            int dataOffsetOffset = (int) f.getFilePointer();
            f.writeInt(0);
            // The final offset serves as a placeholder for sections that might be added in future and
            // ensures we know the size of the final "real" section. Relying on the last section ending at
            // EOF would make it harder to append sections to the end of the file in a backward compatible
            // way.
            int finalOffsetOffset = (int) f.getFilePointer();
            f.writeInt(0);
            int indexOffset = (int) f.getFilePointer();
            // Write the index.
            ArrayList<String> sortedOlsonIds = new ArrayList<String>();
            sortedOlsonIds.addAll(offsets.keySet());
            Collections.sort(sortedOlsonIds);
            for (String zoneName : sortedOlsonIds) {
                if (zoneName.length() >= MAXNAME) {
                    throw new IllegalArgumentException("zone filename too long: " + zoneName.length());
                }
                f.write(toAscii(new byte[MAXNAME], zoneName));
                f.writeInt(offsets.get(zoneName));
                f.writeInt(lengths.get(zoneName));
            }
            int dataOffset = (int) f.getFilePointer();
            // Write the data.
            f.write(allData.toByteArray());
            int finalOffset = (int) f.getFilePointer();
            // Go back and fix up the offsets in the header.
            f.seek(indexOffsetOffset);
            f.writeInt(indexOffset);
            f.seek(dataOffsetOffset);
            f.writeInt(dataOffset);
            f.seek(finalOffsetOffset);
            f.writeInt(finalOffset);
        }
    }

    // Concatenate the contents of 'inFile' onto 'out'.
    private static void copyFile(File inFile, OutputStream out) throws Exception {
        try (InputStream in = new FileInputStream(inFile)) {
            byte[] buf = new byte[8192];
            while (true) {
                int nbytes = in.read(buf);
                if (nbytes == -1) {
                    break;
                }
                out.write(buf, 0, nbytes);
            }
            out.flush();
        }
    }

    private static byte[] toAscii(byte[] dst, String src) {
        for (int i = 0; i < src.length(); ++i) {
            if (src.charAt(i) > '~') {
                throw new IllegalArgumentException("non-ASCII string: " + src);
            }
            dst[i] = (byte) src.charAt(i);
        }
        return dst;
    }

    public static void main(String[] args) throws Exception {
        String setupFilePath = args[0];
        String dataDir = args[1];
        String outputDir = args[2];
        String tzdataVersion = args[3];
        new ZoneCompactor(setupFilePath, dataDir, outputDir, tzdataVersion);
    }
}