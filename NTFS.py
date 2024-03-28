import re
import os
from enum import Flag, auto
from datetime import datetime
from path_handle import *

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

class MFT_record:
    def __init__(self, data) -> None:
        self.raw_data = data
        self.standard_info = {}
        self.file_name = {}
        self.data = {}
        self.childs: list[MFT_record] = []

        self.file_id = int.from_bytes(self.raw_data[0x2C:0x30], byteorder = 'little')
        self.flag = self.raw_data[0x16]
        if self.flag == 0 or self.flag == 2:
            # Deleted record, skip
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
        # system and hidden record is not active
        if NTFSAttribute.SYSTEM in flags or NTFSAttribute.HIDDEN in flags:
            return False
        return True

    def find_record(self, name):
        for child in self.childs:
            if child.file_name['long_name'] == name:
                return child
        return None

    def get_active_records(self) -> 'list[MFT_record]':
        record_list: list[MFT_record] = []
        for record in self.childs:
            if record.is_active():
                record_list.append(record)
        return record_list

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
            offset_offset = start + 0x14
            offset = int.from_bytes(self.raw_data[offset_offset: offset_offset + 2], byteorder='little')

            size_offset = start + 0x10
            size = int.from_bytes(self.raw_data[size_offset: size_offset + 4], byteorder='little')

            content_offset = start + offset
            content = self.raw_data[content_offset: content_offset + size]

            self.data['size'] = size
            self.data['content'] = content
        else:
            cluster_chain_offset = start + 0x40
            cluster_chain = self.raw_data[cluster_chain_offset]
            offset = (cluster_chain & 0xF0) >> 4
            size = cluster_chain & 0x0F

            size_offset = start + 0x30
            size = int.from_bytes(self.raw_data[size_offset: size_offset + 8], byteorder='little')

            cluster_size_offset = start + 0x41
            cluster_size = int.from_bytes(self.raw_data[cluster_size_offset: cluster_size_offset + size], byteorder='little')

            cluster_offset_offset = start + 0x41 + size
            cluster_offset = int.from_bytes(self.raw_data[cluster_offset_offset: cluster_offset_offset + offset], byteorder='little')

            self.data['size'] = size
            self.data['cluster_size'] = cluster_size
            self.data['cluster_offset'] = cluster_offset


class DirTree:
    def __init__(self, nodes: 'list[MFT_record]') -> None:
        self.root = None
        self.nodes_dict: dict[int, MFT_record] = {}
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

    def find_record(self, name: str):
        return self.current_dir.find_record(name)

    def get_parent_record(self, record: MFT_record):
        return self.nodes_dict[record.file_name['parent_id']]

    def get_active_records(self) -> 'list[MFT_record]':
        return self.current_dir.get_active_records()


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
            self.disk_file = open(r'\\.\%s' % self.name, 'rb')
        except (FileNotFoundError, PermissionError, Exception) as e:
            exit()

        try:
            self.boot_sector_raw = self.disk_file.read(0x200)
            self.boot_sector = {}
            self.read_boot_sector()

            if self.boot_sector["Type"] != b'NTFS    ':
                raise Exception

            self.boot_sector["Type"] = self.boot_sector["Type"].decode()
            self.sectors_per_cluster = self.boot_sector["Sectors per cluster"]
            self.bytes_per_sector = self.boot_sector["Bytes per sector"]

            self.record_size = self.boot_sector["Bytes of one MFT"]
            self.mft_offset = self.boot_sector["First cluster of MFT"]
            self.disk_file.seek(self.mft_offset * self.sectors_per_cluster * self.bytes_per_sector)
            
            self.mft_file = MFT_file(self.disk_file.read(self.record_size))
            mft_record: list[MFT_record] = []
            for _ in range(2, self.mft_file.num_sector, 2):
                entry_data = self.disk_file.read(self.record_size)
                if entry_data[:4] == b"FILE":
                    try:
                        mft_record.append(MFT_record(entry_data))
                    except Exception as e:
                        pass

            self.dir_tree = DirTree(mft_record)
        except Exception as e:
            exit()

    @staticmethod
    def is_ntfs(name: str):
        try:
            with open(r'\\.\%s' % name, 'rb') as disk_file:
                Type_ID = disk_file.read(0xB)[3:]
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
  
    def visit_dir(self, path) -> MFT_record:
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
                cur_dir = self.dir_tree.get_parent_record(cur_dir)
                continue
            elif d == ".":
                continue
            record = cur_dir.find_record(d)

            if record is None:
                raise Exception("Directory not found!")
            
            if record.is_directory():
                cur_dir = record
            else:
                raise Exception("Not a directory")
        return cur_dir

    # def get_all_record(self, path = ""):
    #     if path != "":
    #         next_dir = self.visit_dir(path)
    #         record_list = next_dir.get_active_records()
    #     else:
    #         record_list = self.dir_tree.get_active_records()
    #     return record_list

    # def get_items(self, path = ""):
    #     items = []
    #     record_list = self.get_all_record(path)
    #     for record in record_list:
    #         items.append(record.file_name['long_name'])
    #     return items

    # def get_dir(self, path = ""):
    #     try:
    #         record_list = self.get_all_record(path)
    #         ret = []
    #         for record in record_list:
    #             obj = {}
    #             obj["Flags"] = record.standard_info['flags'].value
    #             obj["Name"] = record.file_name['long_name']
    #             ret.append(obj)
    #         return ret
    #     except Exception as e:
    #         raise (e)

    def change_dir(self, full_path=""):
        if full_path == "":
            raise Exception("Path to directory is required!")

        # if full_path == "~":
        #     full_path = self.name

        try:
            next_dir = self.visit_dir(full_path)
            self.dir_tree.current_dir = next_dir

            dirs = self.get_path(full_path)
            if dirs[0] == self.name:
                self.cwd.clear()
                self.cwd.append(self.name)
                dirs.pop(0)

            # for d in dirs:
            #     if d == "..":
            #         if len(self.cwd) > 1:
            #             self.cwd.pop()
            #     elif d != ".":
            #         self.cwd.append(d)
        except Exception as e:
            pass

    def cal_total_directory_bytes(self, record):
        total_bytes = 0
        for child in record.childs:
            if child.is_directory():
                total_bytes += self.cal_total_directory_bytes(child)
            elif 'size' in child.data:
                total_bytes += child.data['size']
        return total_bytes

    def get_folder_file_information(self, path, key):
        try:
            # is folder
            if key == 0:
                cur_dir = self.visit_dir(path)
                record = cur_dir
            # is file
            else:
                cur_dir = self.visit_dir(get_parent_path(path))
                file_name = os.path.basename(path)
                record = cur_dir.find_record(file_name)

            obj = {}
            obj["Flags"] = record.standard_info['flags'].value
            obj["Date Created"] = record.standard_info['created_time'].strftime("%d/%m/%Y")
            obj["Time Created"] = record.standard_info['created_time'].strftime("%H:%M:%S")
            obj["Date Modified"] = record.standard_info['last_modified_time'].strftime("%d/%m/%Y")
            obj["Time Modified"] = record.standard_info['last_modified_time'].strftime("%H:%M:%S")
            obj["Name"] = record.file_name['long_name']
            obj["Attribute"] = record.standard_info["flags"]
            if record.is_directory():
                obj["Bytes"] = self.cal_total_directory_bytes(record)
            elif 'size' in record.data:
                obj["Bytes"] = record.data['size']
            else:
                obj["Bytes"] = 0

            if record.data['resident']:
                obj["Sector"] = self.mft_offset * self.sectors_per_cluster + record.file_id
            else:
                obj["Sector"] = record.data['cluster_offset'] * self.sectors_per_cluster

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
            record = next_dir.find_record(name)
        else:
            record = self.dir_tree.find_record(path[0])

        # File doesn't exist
        if record is None:
            raise Exception
        if record.is_directory():
            raise Exception
        if 'resident' not in record.data:
            return ''
        if record.data['resident']:
            try:
                data = record.data['content'].decode()
            # Not a text file
            except UnicodeDecodeError as e:
                raise (e)
            except Exception as e:
                raise (e)
            return data
        else:
            data = ""
            size_left = record.data['size']
            offset = record.data['cluster_offset'] * self.sectors_per_cluster * self.bytes_per_sector
            cluster_num = record.data['cluster_size']
            self.disk_file.seek(offset)
            for _ in range(cluster_num):
                if size_left <= 0:
                    break
                raw_data = self.disk_file.read(min(self.sectors_per_cluster * self.bytes_per_sector, size_left))
                size_left -= self.sectors_per_cluster * self.bytes_per_sector
                try:
                    data += raw_data.decode()
                except UnicodeDecodeError as e:
                    raise (e)
                except Exception as e:
                    raise (e)
            return data

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
        if getattr(self, "disk_file", None):
            self.disk_file.close()