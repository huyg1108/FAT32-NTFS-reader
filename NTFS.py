import re
import os
from enum import Flag, auto
from datetime import datetime
from path_handle import *
import subprocess
import sys

def format_time(timestamp):
    return datetime.fromtimestamp((timestamp - 116444736000000000) // 10000000)

class NTFSAttribute(Flag):
    READ_ONLY = auto()
    HIDDEN = auto()
    SYSTEM = auto()
    VOLLABLE = auto()
    DIRECTORY = auto()
    ARCHIVE = auto()
    DEVICE = auto()
    NORMAL = auto()
    TEMPORARY = auto()
    SPARSE_FILE = auto()
    REPARSE_POINT = auto()
    COMPRESSED = auto()
    OFFLINE = auto()
    NOT_INDEXED = auto()
    ENCRYPTED = auto()

class MFTentry:
    def __init__(self, data) -> None:
        self.raw_data = data
        self.standard_info = {}
        self.file_name = {}
        self.data = {}
        self.childs: list[MFTentry] = []

        self.file_id = int.from_bytes(self.raw_data[0x2C:0x30], byteorder = 'little')
        self.flag = self.raw_data[0x16]
        if self.flag == 0 or self.flag == 2:
            raise Exception

        standard_info_start = int.from_bytes(self.raw_data[0x14:0x16], byteorder = 'little')
        standard_info_size = int.from_bytes(self.raw_data[standard_info_start + 4:standard_info_start + 8], byteorder = 'little')
        self.get_standard_info(standard_info_start)
        
        file_name_start = standard_info_start + standard_info_size
        file_name_size = int.from_bytes(self.raw_data[file_name_start + 4:file_name_start + 8], byteorder = 'little')
        self.get_file_name(file_name_start)
        
        data_start = file_name_start + file_name_size
        data_sign = self.raw_data[data_start:data_start + 4]
        if data_sign[0] == 64:
            data_start += int.from_bytes(self.raw_data[data_start + 4:data_start + 8], byteorder = 'little')

        data_sign = self.raw_data[data_start:data_start + 4]
        if data_sign[0] == 128:
            self.get_data(data_start)
        elif data_sign[0] == 144:
            self.standard_info['flags'] |= NTFSAttribute.DIRECTORY
            self.data['size'] = 0
            self.data['resident'] = True

        del self.raw_data

    def is_directory(self):
        return NTFSAttribute.DIRECTORY in self.standard_info['flags']

    def is_leaf(self):
        return not len(self.childs)

    def is_active(self):
        flags = self.standard_info['flags']
        # system and hidden entry is not active
        if NTFSAttribute.SYSTEM in flags or NTFSAttribute.HIDDEN in flags:
            return False
        return True

    def find_entry(self, name):
        for child in self.childs:
            if child.file_name['long_name'] == name:
                return child
        return None

    def get_active_entries(self) -> 'list[MFTentry]':
        entry_list: list[MFTentry] = []
        for entry in self.childs:
            if entry.is_active():
                entry_list.append(entry)
        return entry_list

    # 0x10
    def get_standard_info(self, start):
        sign = int.from_bytes(self.raw_data[start:start + 4], byteorder = 'little')
        if sign != 0x10:
            raise Exception
        offset = int.from_bytes(self.raw_data[start + 20:start + 21], byteorder = 'little')
        begin = start + offset
        self.standard_info["created_time"] = format_time(int.from_bytes(self.raw_data[begin:begin + 8], byteorder = 'little'))
        self.standard_info["last_modified_time"] = format_time(int.from_bytes(self.raw_data[begin + 8:begin + 16], byteorder = 'little'))
        self.standard_info["flags"] = NTFSAttribute(int.from_bytes(self.raw_data[begin + 32:begin + 36], byteorder = 'little') & 0xFFFF)

    # 0x30
    def get_file_name(self, start):
        sign = int.from_bytes(self.raw_data[start:start + 4], byteorder='little')
        if sign != 0x30:
            raise Exception

        size_offset = start + 0x10
        size = int.from_bytes(self.raw_data[size_offset: size_offset + 4], byteorder='little')

        offset_offset = start + 0x14
        offset = int.from_bytes(self.raw_data[offset_offset: offset_offset + 2], byteorder='little')

        parent_id_offset = start + offset
        parent_id = int.from_bytes(self.raw_data[parent_id_offset: parent_id_offset + 6], byteorder='little')

        name_length_offset = parent_id_offset + 64
        name_length = self.raw_data[name_length_offset]

        long_name_offset = name_length_offset + 2
        long_name = self.raw_data[long_name_offset: long_name_offset + name_length * 2].decode('utf-16le')

        self.file_name["parent_id"] = parent_id
        self.file_name["name_length"] = name_length
        self.file_name["long_name"] = long_name

    # 0x80
    def get_data(self, start):
        self.data['resident'] = not bool(self.raw_data[start + 0x8])
        if self.data['resident']:
            offset = int.from_bytes(self.raw_data[start + 0x14:start + 0x16], byteorder='little')
            self.data['size'] = int.from_bytes(self.raw_data[start + 0x10:start + 0x14], byteorder='little')
            self.data['content'] = self.raw_data[start + offset:start + offset + self.data['size']]
        
        else:
            self.data['size'] = int.from_bytes(self.raw_data[start + 0x30: start + 0x38], byteorder='little')
            test = self.data['size']
            offset = int.from_bytes(self.raw_data[start + 0x40: start + 0x41], byteorder='little')
            
            self.data['data_run'] = []
            flag = 1
            i = 0

            while True:
                if flag == 0:
                    break
                
                if i == 0:
                    cluster_chain = self.raw_data[start + 0x40]
                    offset = (cluster_chain & 0xF0) >> 4
                    size = cluster_chain & 0x0F

                    cluster_count = int.from_bytes(self.raw_data[start + 0x41: start + 0x41 + size], byteorder='little')
                    first_cluster =  int.from_bytes(self.raw_data[start + 0x41 + size: start + 0x41 + size + offset], byteorder='little')
                    
                    flag = int.from_bytes(self.raw_data[start + 0x41 + size + offset: start + 0x41 + size + offset + 0x1], byteorder='little')
                    start += 0x41 + size + offset
                
                else:
                    cluster_chain = self.raw_data[start]
                    offset = (cluster_chain & 0xF0) >> 4
                    size = cluster_chain & 0x0F

                    cluster_count = int.from_bytes(self.raw_data[start + 0x1: start + 0x1 + size], byteorder='little')
                    first_cluster += int.from_bytes(self.raw_data[start + 0x1 + size: start + 0x1 + size + offset], byteorder='little', signed = True)
                    
                    flag = int.from_bytes(self.raw_data[start + 0x1 + size + offset: start + 0x2 + size + offset], byteorder='little')
                
                i += 1
                self.data['data_run'].append([cluster_count, first_cluster])

class DirTree:
    def __init__(self, nodes: 'list[MFTentry]') -> None:
        self.root = None
        self.nodes_dict: dict[int, MFTentry] = {}
        for node in nodes:
            self.nodes_dict[node.file_id] = node

        for key in self.nodes_dict:
            parent_id = self.nodes_dict[key].file_name['parent_id']
            if parent_id in self.nodes_dict:
                self.nodes_dict[parent_id].childs.append(self.nodes_dict[key])

        for key in self.nodes_dict:
            parent_id = self.nodes_dict[key].file_name['parent_id']
            if parent_id == self.nodes_dict[key].file_id:
                self.root = self.nodes_dict[key]
                break

        self.current_dir = self.root

    def find_entry(self, name: str):
        return self.current_dir.find_entry(name)

    def get_parent_entry(self, entry: MFTentry):
        return self.nodes_dict[entry.file_name['parent_id']]

    def get_active_entries(self) -> 'list[MFTentry]':
        return self.current_dir.get_active_entries()


class MFT_file:
    def __init__(self, data: bytes) -> None:
        self.raw_data = data
        self.info_offset = int.from_bytes(self.raw_data[0x14:0x16], byteorder = 'little')
        self.info_len = int.from_bytes(self.raw_data[0x3C:0x40], byteorder = 'little')

        self.file_name_offset = self.info_offset + self.info_len
        self.file_name_len = int.from_bytes(self.raw_data[0x9C:0xA0], byteorder = 'little')

        self.data_offset = self.file_name_offset + self.file_name_len
        self.data_len = int.from_bytes(self.raw_data[0x104:0x108], byteorder = 'little')
        self.num_sector = (int.from_bytes(self.raw_data[0x118:0x120], byteorder = 'little') + 1) * 8
        del self.raw_data

class NTFS:
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
            self.read_boot_sector()

            if self.boot_sector["Type"] != b'NTFS    ':
                raise Exception

            self.boot_sector["Type"] = self.boot_sector["Type"].decode()
            self.sectors_per_cluster = self.boot_sector["Sectors per cluster"]
            self.bytes_per_sector = self.boot_sector["Bytes per sector"]

            self.entry_size = self.boot_sector["Bytes of one MFT"]
            self.mft_offset = self.boot_sector["First cluster of MFT"]

            self.fd.seek(self.mft_offset * self.sectors_per_cluster * self.bytes_per_sector)

            # First part of MFT is MFT file
            self.mft_file = MFT_file(self.fd.read(self.entry_size))

            mftentry: list[MFTentry] = []
            for _ in range(2, self.mft_file.num_sector, 2):
                entry_data = self.fd.read(self.entry_size)
                if entry_data[:4] == b"FILE":
                    try:
                        mftentry.append(MFTentry(entry_data))
                    except Exception as e:
                        pass

            self.dir_tree = DirTree(mftentry)
        except Exception as e:
            exit()

    def mft_header_offset(self, target_entry: MFTentry):
        try:
            if target_entry is None:
                print(f"Folder not found.")
                return

            mft_start_offset = self.mft_offset * self.sectors_per_cluster * self.bytes_per_sector
            entry_offset = mft_start_offset + (target_entry.file_id * self.entry_size)
            
            return entry_offset
        except Exception as e:
            raise e


    @staticmethod
    def is_ntfs(name: str):
        try:
            with open(r'\\.\%s' % name, 'rb') as fd:
                Type_ID = fd.read(0xB)[3:]
                if Type_ID == b'NTFS    ':
                    return True
                return False
        except Exception as e:
            exit()

    def read_boot_sector(self):
        self.boot_sector['Type'] = self.boot_sector_raw[3:0xB]
        self.boot_sector['Bytes per sector'] = int.from_bytes(self.boot_sector_raw[0xB:0xD], byteorder = 'little')
        self.boot_sector['Sectors per cluster'] = int.from_bytes(self.boot_sector_raw[0xD:0xE], byteorder = 'little')
        self.boot_sector['Sectors per track'] = int.from_bytes(self.boot_sector_raw[0x18:0x1A], byteorder = 'little')
        self.boot_sector['Number of heads'] = int.from_bytes(self.boot_sector_raw[0x1A:0x1C], byteorder = 'little')
        self.boot_sector['Total sectors in volume'] = int.from_bytes(self.boot_sector_raw[0x28:0x30], byteorder = 'little')
        self.boot_sector['First cluster of MFT'] = int.from_bytes(self.boot_sector_raw[0x30:0x38], byteorder = 'little')
        self.boot_sector['First cluster of Mirror MFT'] = int.from_bytes(self.boot_sector_raw[0x38:0x40], byteorder = 'little')
        self.boot_sector['Bytes of one MFT'] = 2 ** abs(int.from_bytes(self.boot_sector_raw[0x40:0x41], byteorder = 'little', signed=True))

    def get_path(self, path):
        dirs = re.sub(r"[/\\]+", r"\\", path).strip("\\").split("\\")
        return dirs
  
    def visit_dir(self, path) -> MFTentry:
        if path == "":
            raise Exception("Directory name is required!")
        path = self.get_path(path)

        if path[0] == self.name:
            cur_dir = self.dir_tree.root
            path.pop(0)
        else:
            cur_dir = self.dir_tree.current_dir
        for d in path:
            if d == "..":
                cur_dir = self.dir_tree.get_parent_entry(cur_dir)
                continue
            elif d == ".":
                continue
            entry = cur_dir.find_entry(d)

            if entry is None:
                raise Exception("Directory not found!")
            
            if entry.is_directory():
                cur_dir = entry
            else:
                raise Exception("Not a directory")
        return cur_dir

    def get_all_entry(self, path = ""):
        if path != "":
            next_dir = self.visit_dir(path)
            entry_list = next_dir.get_active_entries()
        else:
            entry_list = self.dir_tree.get_active_entries()
        return entry_list

    def get_items(self, path = ""):
        items = []
        entry_list = self.get_all_entry(path)
        for entry in entry_list:
            items.append(entry.file_name['long_name'])
        return items

    def get_dir(self, path = ""):
        try:
            entry_list = self.get_all_entry(path)
            ret = []
            for entry in entry_list:
                obj = {}
                obj["Flags"] = entry.standard_info['flags'].value
                obj["Name"] = entry.file_name['long_name']
                ret.append(obj)
            return ret
        except Exception as e:
            raise (e)

    def change_dir(self, full_path=""):
        if full_path == "":
            raise Exception("Path to directory is required!")
        try:
            next_dir = self.visit_dir(full_path)
            self.dir_tree.current_dir = next_dir

            dirs = self.get_path(full_path)
            if dirs[0] == self.name:
                self.cwd.clear()
                self.cwd.append(self.name)
                dirs.pop(0)
        except Exception as e:
            pass

    def get_folder_file_information(self, path: str, key):
        try:
            # is folder
            if key == 0:
                cur_dir = self.visit_dir(path)
                entry = cur_dir
            # is file
            else:
                cur_dir = self.visit_dir(get_parent_path(path))
                file_name = os.path.basename(path)
                entry = cur_dir.find_entry(file_name)

            obj = {}
            obj["Flags"] = entry.standard_info['flags'].value
            obj["Date Created"] = entry.standard_info['created_time'].strftime("%d/%m/%Y")
            obj["Time Created"] = entry.standard_info['created_time'].strftime("%H:%M:%S")
            obj["Date Modified"] = entry.standard_info['last_modified_time'].strftime("%d/%m/%Y")
            obj["Time Modified"] = entry.standard_info['last_modified_time'].strftime("%H:%M:%S")
            obj["Name"] = entry.file_name['long_name']
            obj["Attribute"] = entry.standard_info["flags"]
            obj["Bytes"] = entry.data['size']

            return obj
        except Exception as e:
            raise (e)


    def get_cwd(self):
        if len(self.cwd) == 1:
            return self.cwd[0] + "\\"
        return "\\".join(self.cwd)


    # Read content of .txt
    def get_text_content(self, path: str) -> str:
        path = self.get_path(path)
        if len(path) > 1:
            name = path[-1]
            path = "\\".join(path[:-1])
            next_dir = self.visit_dir(path)
            entry = next_dir.find_entry(name)
        else:
            entry = self.dir_tree.find_entry(path[0])

        # File doesn't exist
        if entry is None:
            raise Exception
        if entry.is_directory():
            raise Exception
        if 'resident' not in entry.data:
            return ''
        if entry.data['resident']:
            try:
                data = entry.data['content'].decode()
            # Not a text file
            except UnicodeDecodeError as e:
                raise (e)
            except Exception as e:
                raise (e)
            return data
        else:
            data = ""
            size_left = entry.data['size']
            offset = 0
            cluster_num = 0
            
            # 0: cluster_count, 1: first_cluster
            for data_run in entry.data['data_run']:
                if cluster_num == 0:
                    first_run_offset = data_run[1]
                    offset = first_run_offset * self.sectors_per_cluster * self.bytes_per_sector
                else:
                    diff = data_run[1] - (first_run_offset)
                    offset += diff * self.sectors_per_cluster * self.bytes_per_sector

                self.fd.seek(offset)

                cluster_num = data_run[0]

                for i in range(cluster_num):
                    if size_left <= 0:
                        break
                    raw_data = self.fd.read(min(self.sectors_per_cluster * self.bytes_per_sector, size_left))
                    size_left -= self.sectors_per_cluster * self.bytes_per_sector
                    try:
                        data += raw_data.decode()
                    except UnicodeDecodeError as e:
                        raise (e)
                    except Exception as e:
                        raise (e)
        
            return data

    def delete_folder_file(self, path: str, key):
        try:
            # is folder
            if key == 0:
                cur_dir = self.visit_dir(path)
                entry = cur_dir
            # is file
            else:
                cur_dir = self.visit_dir(get_parent_path(path))
                file_name = os.path.basename(path)
                entry = cur_dir.find_entry(file_name)

            subprocess.call(["delete.exe", self.name, "DEL", "NTFS", str(self.mft_header_offset(entry)), str(self.entry_size)])
        except Exception as e:
            raise (e)

    main_components = [
        "Type",
        "Bytes per sector",
        "Sectors per cluster", 
        "Sectors per track",
        "Number of heads",
        "Total sectors in volume",
        "First cluster of MFT",
        "First cluster of Mirror MFT",
        "Bytes of one MFT"
    ]

    def __str__(self) -> str:
        s = "Volume name: " + self.name + "\n"
        for key in NTFS.main_components:
            s += f"{key}: {self.boot_sector[key]}\n"
        return s

    def __del__(self):
        if getattr(self, "fd", None):
            self.fd.close()
