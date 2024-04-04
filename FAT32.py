from enum import Flag, auto
from datetime import datetime
from itertools import chain
import re
import os
from path_handle import *
import subprocess
import sys

# thông tin của một entry
class Attribute(Flag):
    READ_ONLY = auto()
    HIDDEN = auto()
    SYSTEM = auto()
    VOLLABLE = auto()
    DIRECTORY = auto()
    ARCHIVE = auto()

class RDETentry:
    def __init__(self, data) -> None:
        self.raw_data = data
        self.flag = data[0xB:0xC]
        self.is_subentry: bool = self.check_subentry()
        self.is_deleted: bool = False
        self.is_empty: bool = False
        self.is_label: bool = False
        self.attr = Attribute(0)
        self.size = 0
        self.date_created = 0
        self.date_updated = 0
        self.name = b""
        self.ext = b""
        self.long_name = ""
        self.starting_offset = 0

        if not self.is_subentry:
            self.name = self.raw_data[:0x8]
            self.ext = self.raw_data[0x8:0xB]
            if self.name[:1] == b'\xe5':
                self.is_deleted = True
            if self.name[:1] == b'\x00':
                self.is_empty = True
                self.name = ""
                return
            
            self.attr = Attribute(int.from_bytes(self.flag, byteorder='little'))
            if Attribute.VOLLABLE in self.attr:
                self.is_label = True
                return

            self.time_created_raw = int.from_bytes(self.raw_data[0xD:0x10], byteorder='little')
            self.date_created_raw = int.from_bytes(self.raw_data[0x10:0x12], byteorder='little')
            self.time_updated_raw = int.from_bytes(self.raw_data[0x16:0x18], byteorder='little')
            self.date_updated_raw = int.from_bytes(self.raw_data[0x18:0x1A], byteorder='little')

            self.extract_raw_created()
            self.extract_raw_updated()

            # https://people.cs.umass.edu/~liberato/courses/2017-spring-compsci365/lecture-notes/11-fats-and-directory-entries/
            # why this line is written like this
            self.start_cluster = int.from_bytes(self.raw_data[0x14:0x16][::-1] + self.raw_data[0x1A:0x1C][::-1], byteorder='big') 
            self.size = int.from_bytes(self.raw_data[0x1C:0x20], byteorder='little')

        else:
            self.index = self.raw_data[0]
            self.name = b""
            for i in chain(range(0x1, 0xB), range(0xE, 0x1A), range(0x1C, 0x20)):
                self.name += int.to_bytes(self.raw_data[i], 1, byteorder='little')
                if self.name.endswith(b"\xff\xff"):
                    self.name = self.name[:-2]
                    break
            self.name = self.name.decode('utf-16le').strip('\x00')

    def check_subentry(self) -> bool:
        if self.flag == b'\x0f':
            self.is_subentry = True
            return True
        return False

    def extract_raw_created(self):
        h = (self.time_created_raw & 0b111110000000000000000000) >> 19
        m = (self.time_created_raw & 0b000001111110000000000000) >> 13
        s = (self.time_created_raw & 0b000000000001111110000000) >> 7
        year = 1980 + ((self.date_created_raw & 0b1111111000000000) >> 9)
        mon = (self.date_created_raw & 0b0000000111100000) >> 5
        day = self.date_created_raw & 0b0000000000011111

        self.date_created = datetime(year, mon, day, h, m, s)

    def extract_raw_updated(self):
        h = (self.time_updated_raw & 0b1111100000000000) >> 11
        m = (self.time_updated_raw & 0b0000011111100000) >> 5
        s = (self.time_updated_raw & 0b0000000000011111) * 2
        year = 1980 + ((self.date_updated_raw & 0b1111111000000000) >> 9)
        mon = (self.date_updated_raw & 0b0000000111100000) >> 5
        day = self.date_updated_raw & 0b0000000000011111

        self.date_updated = datetime(year, mon, day, h, m, s)

    def is_active_entry(self) -> bool:
        return not (self.is_empty or self.is_subentry or self.is_deleted or self.is_label or Attribute.SYSTEM in self.attr)
    
    def is_directory(self) -> bool:
        return Attribute.DIRECTORY in self.attr

    def is_archive(self) -> bool:
        return Attribute.ARCHIVE in self.attr

class RDET:
    def __init__(self, data: bytes,starting_offset) -> None:
        self.raw_data: bytes = data
        self.entries: list[RDETentry] = []
        long_name = ""
        for i in range(0, len(data), 32):
            self.entries.append(RDETentry(self.raw_data[i: i + 32]))
            self.entries[-1].starting_offset = i + starting_offset
            if self.entries[-1].is_empty or self.entries[-1].is_deleted:
                long_name = ""
                continue
            if self.entries[-1].is_subentry:
                long_name = self.entries[-1].name + long_name
                continue

            if long_name != "":
                self.entries[-1].long_name = long_name
            else:
                extend = self.entries[-1].ext.strip().decode()
                if extend == "":
                    self.entries[-1].long_name = self.entries[-1].name.strip().decode()
                else:
                    self.entries[-1].long_name = self.entries[-1].name.strip().decode() + "." + extend
            long_name = ""
            # print(self.entries[-1].long_name, self.entries[-1].starting_offset)

    def get_active_entries(self) -> 'list[RDETentry]':
        entry_list = []
        for i in range(len(self.entries)):
            if self.entries[i].is_active_entry():
                entry_list.append(self.entries[i])
        return entry_list

    def find_entry(self, name) -> RDETentry:
        for i in range(len(self.entries)):
            if self.entries[i].is_active_entry() and self.entries[i].long_name.lower() == name.lower():
                return self.entries[i]
        return None

class FAT:
    def __init__(self, data) -> None:
        self.raw_data = data
        self.elements = []
        for i in range(0, len(self.raw_data), 4):
            self.elements.append(int.from_bytes(self.raw_data[i:i + 4], byteorder='little'))
  
    def get_cluster_chain(self, index: int) -> 'list[int]':
        index_list = []
        while True:
            index_list.append(index)
            index = self.elements[index]
            if index == 0x0FFFFFFF or index == 0x0FFFFFF7:
                break
        return index_list


class FAT32:
    def __init__(self, name: str) -> None:
        self.name = name
        self.cwd = [self.name]
        try:
            self.fd = open(r'\\.\%s' % self.name, 'rb')
        except (FileNotFoundError, PermissionError, Exception) as e:
            exit()
        
        try:
            self.boot_sector_raw = self.fd.read(0x200)
            self.boot_sector = {}
            self.extract_boot_sector()
            if self.boot_sector["FAT type"] != b"FAT32   ":
                raise Exception("Not FAT32")
            self.boot_sector["FAT type"] = self.boot_sector["FAT type"].decode()
            self.SB = self.boot_sector['Sectors before FAT table']
            self.SF = self.boot_sector["Sectors Per FAT"]
            self.NF = self.boot_sector["Number of FAT table"]
            self.SC = self.boot_sector["Sectors Per Cluster"]
            self.BS = self.boot_sector["Bytes Per Sector"]
            self.boot_sector_reserved_raw = self.fd.read(self.BS * (self.SB - 1))
            
            FAT_size = self.BS * self.SF
            self.FAT: list[FAT] = []
            for _ in range(self.NF):
                self.FAT.append(FAT(self.fd.read(FAT_size)))

            self.DET = {}
            
            start = self.boot_sector["Starting Cluster of RDET"]
            # print("vị trí bắt đầu của RDET là", self.offset_from_cluster(start) * self.BS)
            self.DET[start] = RDET(self.get_all_cluster_data(start),self.offset_from_cluster(start) * self.BS)
            self.RDET = self.DET[start]

        except Exception as e:
            exit()
    
    @staticmethod
    def check_fat32(name: str):
        try:
            with open(r'\\.\%s' % name, 'rb') as fd:
                fd.read(1)
                fd.seek(0x52)
                fat_name = fd.read(8)
                if fat_name == b"FAT32   ":
                    return True
                return False
        except Exception as e:
            exit()

    def extract_boot_sector(self):
        self.boot_sector['Bytes Per Sector'] = int.from_bytes(self.boot_sector_raw[0xB:0xD], byteorder='little')
        self.boot_sector['Sectors Per Cluster'] = int.from_bytes(self.boot_sector_raw[0xD:0xE], byteorder='little')
        self.boot_sector['Sectors before FAT table'] = int.from_bytes(self.boot_sector_raw[0xE:0x10], byteorder='little')
        self.boot_sector['Number of FAT table'] = int.from_bytes(self.boot_sector_raw[0x10:0x11], byteorder='little')
        self.boot_sector['Volume size'] = int.from_bytes(self.boot_sector_raw[0x20:0x24], byteorder='little')
        self.boot_sector['Sectors Per FAT'] = int.from_bytes(self.boot_sector_raw[0x24:0x28], byteorder='little')
        self.boot_sector['Starting Cluster of RDET'] = int.from_bytes(self.boot_sector_raw[0x2C:0x30], byteorder='little')
        self.boot_sector['FAT type'] = self.boot_sector_raw[0x52:0x5A]
    # offset from the start of the file to the start of the cluster
    # return formula: Number Sector of Boot Sector + Number Sector of FAT table * Sector of FAT + (index - 2) * Number Sector of Cluster
    def offset_from_cluster(self, index):
        return self.SB + self.SF * self.NF + (index - 2) * self.SC
    
    def format_path(self, path):
        dirs = re.sub(r"[/\\]+", r"\\", path).strip("\\").split("\\")
        return dirs

    # get current working directory
    def get_cwd(self):
        if len(self.cwd) == 1:
            return self.cwd[0] + "\\"
        return "\\".join(self.cwd)

    def visit_dir(self, dir) -> RDET:
        if dir == "":
            raise Exception("Directory name is required!")
        dirs = self.format_path(dir)

        if dirs[0] == self.name:
            cdet = self.DET[self.boot_sector["Starting Cluster of RDET"]]
            dirs.pop(0)
        else:
            cdet = self.RDET

        for d in dirs:
            entry = cdet.find_entry(d)
            if entry is None:
                raise Exception("Directory not found!")
            if entry.is_directory():
                if entry.start_cluster == 0:
                    cdet = self.DET[self.boot_sector["Starting Cluster of RDET"]]
                    continue
                if entry.start_cluster in self.DET:
                    cdet = self.DET[entry.start_cluster]
                    continue
                self.DET[entry.start_cluster] = RDET(self.get_all_cluster_data(entry.start_cluster), self.offset_from_cluster(entry.start_cluster) * self.BS)
                cdet = self.DET[entry.start_cluster] 
            else:
                raise Exception("Not a directory")
        return cdet

    def change_dir(self, path=""):
        if path == "":
            raise Exception("Path to directory is required!")
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.get_cwd(), path)
                
            if os.path.isdir(path):
                cdet = self.visit_dir(path)
            else:
                cdet = self.visit_dir(os.path.dirname(path))
                
            self.RDET = cdet

            dirs = self.format_path(path)
            if dirs[0] == self.name:
                self.cwd.clear()
                self.cwd.append(self.name)
                dirs.pop(0)
        except Exception as e:
            raise(e)

    def get_folder_file_information(self, path, key):
        try:
            obj = {}
            if key == 0:
                if not os.path.isabs(path):
                    path = os.path.join(self.get_cwd(), path)
                cdet = self.visit_dir(os.path.dirname(path))
                file_name = os.path.basename(path)
                record = cdet.find_entry(file_name)
            else:
                # is file
                cdet = self.visit_dir(get_parent_path(path))
                file_name = os.path.basename(path)
                record = cdet.find_entry(file_name)

            obj["Flags"] = record.attr.value
            obj["Date Created"] = record.date_created.strftime("%d/%m/%Y")
            obj["Time Created"] = record.date_created.strftime("%H:%M:%S")
            obj["Date Modified"] = record.date_updated.strftime("%d/%m/%Y")
            obj["Time Modified"] = record.date_updated.strftime("%H:%M:%S")
            obj["Bytes"] = record.size
            obj["Name"] = record.long_name
            obj["Attribute"] = record.attr

            print(record.starting_offset)

            if record.start_cluster == 0:
                obj["Sector"] = (record.start_cluster + 2) * self.SC
            else:
                obj["Sector"] = record.start_cluster * self.SC

            return obj
        except Exception as e:
            raise (e)

    def get_all_cluster_data(self, cluster_index):
        index_list = self.FAT[0].get_cluster_chain(cluster_index)
        data = b""
        for i in index_list:
            off = self.offset_from_cluster(i)
            self.fd.seek(off * self.BS)
            # data = sector per cluster * bytes per sector
            data += self.fd.read(self.SC * self.BS)
        return data

    # Read content of .txt
    def get_text_content(self, path: str) -> str:
        path = self.format_path(path)
        if len(path) > 1:
            name = path[-1]
            path = "\\".join(path[:-1])
            cdet = self.visit_dir(path)
            entry = cdet.find_entry(name)
        else:
            entry = self.RDET.find_entry(path[0])

        if entry is None:
            raise Exception("File doesn't exist")
        if entry.is_directory():
            raise Exception("Is a directory")

        try:
            index_list = self.FAT[0].get_cluster_chain(entry.start_cluster)
            data = ""
            size_left = entry.size
            for i in index_list:
                if size_left <= 0:
                    break
                off = self.offset_from_cluster(i)
                self.fd.seek(off * self.BS)
                raw_data = self.fd.read(min(self.SC * self.BS, size_left))
                size_left -= self.SC * self.BS                
                try:
                    data += raw_data.decode()
                except UnicodeDecodeError as e:
                    raise Exception("Not a text file, please use appropriate software to open.")
                except Exception as e:
                    raise(e)
            return data
        except:
            return ''

    def delete_folder_file(self, path: str, key):
        try:
            if key == 0:
                if not os.path.isabs(path):
                    path = os.path.join(self.get_cwd(), path)
                cdet = self.visit_dir(os.path.dirname(path))
                file_name = os.path.basename(path)
                record = cdet.find_entry(file_name)
            else:
                cdet = self.visit_dir(get_parent_path(path))
                file_name = os.path.basename(path)
                record = cdet.find_entry(file_name)
            subprocess.call(["delete.exe", self.name, str(record.starting_offset), "1"])

        except Exception as e:
            raise (e)

    main_components = [
        "Bytes Per Sector",
        "Sectors Per Cluster", 
        "Sectors before FAT table", 
        "Number of FAT table",
        "Sectors Per FAT",
        "Volume size",
        "Starting Cluster of RDET",
        "FAT type"
    ]

    def __str__(self) -> str:
        s = "Volume name: " + self.name + "\n"
        for key in FAT32.main_components:
            s += f"{key}: {self.boot_sector[key]}\n"
        return s

    def __del__(self):
        if getattr(self, "fd", None):
            self.fd.close()