# import tkinter as tk
# from tkinter import ttk, messagebox
# import os
# from typing import Union
# from NTFS import NTFS
# from FAT32 import FAT32

# def is_folder(folder_path):
#     drive, path = os.path.splitdrive(folder_path)
#     if path and len(path.strip(os.path.sep)) > 0:
#         return True # folder
#     else:
#         return False # disk

# class FolderExplorer(tk.Tk):
#     def __init__(self, volume: Union[FAT32, NTFS]) -> None:
#         super().__init__()
#         self.title("Folder Explorer")
#         self.geometry("800x600")

#         self.vol = volume

#         self.folder_path = tk.StringVar(value=self.vol.get_cwd())

#         self.path_entry = ttk.Entry(self, textvariable=self.folder_path, state="readonly")
#         self.path_entry.pack(fill="x", padx=5, pady=2)

#         # main frame
#         self.folder_view_frame = ttk.Frame(self)
#         self.folder_view_frame.pack(fill="both", expand=True)

#         self.info_text = tk.Text(self, height=15, width=70)
#         self.info_text.pack(side="bottom", padx=5, pady=2)

#         self.tree_button = ttk.Button(self, text="Draw Tree", command=self.show_tree)
#         self.tree_button.pack(side="bottom", padx=5, pady=2)

#         self.info_button = ttk.Button(self, text="Show Disk Information", command=self.get_drive_info)
#         self.info_button.pack(side="bottom", padx=5, pady=2)

#         # folder information
#         self.folder_info_frame = ttk.Frame(self)
#         self.folder_info_frame.pack(fill="both", expand=True)

#         self.folder_info_text = tk.Text(self.folder_info_frame, height=10, width=20)
#         self.folder_info_text.pack(side="right", padx=5, pady=2)

#         self.create_folder_view()

#     def get_drive_info(self):
#         try:
#             info_str = str(self.vol)
#             self.info_text.delete("1.0", tk.END)
#             self.info_text.insert(tk.END, info_str)
#         except Exception as e:
#             messagebox.showerror("Error", str(e))

#     def show_folder_info(self, folder_path):
#         try:
#             if is_folder(folder_path):
#                 file = self.vol.get_folder_file_information(os.path.basename(folder_path))

#                 flag = file['Flags']
#                 atts = []

#                 if flag & 0b1:
#                     atts.append('Read-Only')
#                 if flag & 0b10:
#                     atts.append('Hidden')
#                 if flag & 0b100:
#                     atts.append('System')
#                 if flag & 0b1000:
#                     atts.append('Vollable')
#                 if flag & 0b10000:
#                     atts.append('Directory')
#                 if flag & 0b100000:
#                     atts.append('Archive')

#                 info_text = f"Name: {file['Name']}\n"
#                 if atts:
#                     info_text += f"Attribute: {', '.join(atts)}\n"
#                 else:
#                     info_text += "Attribute: None\n"
#                 info_text += f"Date Created: {str(file['Date Created'])}\n"
#                 info_text += f"Date Modified: {str(file['Date Modified'])}\n"
#                 info_text += f"Total Size: {file['Sector']} sector"
#                 self.folder_info_text.delete("1.0", tk.END)
#                 self.folder_info_text.insert(tk.END, info_text)
#             else:
#                 self.folder_info_text.delete("1.0", tk.END)
#         except Exception as e:
#             messagebox.showerror("Error", str(e))

#     def create_folder_view(self):
#         self.clear_folder_view()

#         items = self.get_folder_file_contents(self.folder_path.get())
#         for item in items:
#             item_path = os.path.join(self.folder_path.get(), item)
#             if os.path.isdir(item_path):
#                 item_button = ttk.Button(self.folder_view_frame, text=item, command=lambda i=item: self.show_folder_contents(os.path.join(self.folder_path.get(), i), 0))
#                 item_button.pack(side="top", padx=5, pady=2)
#             else:
#                 if item.lower().endswith('.txt'):
#                     item_label = ttk.Label(self.folder_view_frame, text=item, foreground="blue", cursor="hand2")
#                     item_label.bind("<Button-1>", lambda event, i=item: self.show_txt_file_content(os.path.join(self.folder_path.get(), i)))
#                     item_label.pack(side="top", padx=5, pady=2)
#                 else:
#                     item_label = ttk.Label(self.folder_view_frame, text=item, foreground="black", cursor="hand2")
#                     item_label.bind("<Button-1>", lambda event: messagebox.showerror("Error", "Only .txt files can be opened"))
#                     item_label.pack(side="top", padx=5, pady=2)

#         if self.folder_path.get() != os.path.splitdrive(self.folder_path.get())[0] + "\\":
#             back_button = ttk.Button(self.folder_view_frame, text="Back", command=self.show_parent_folder)
#             back_button.pack(side="top", padx=5, pady=5)


#     def show_folder_contents(self, folder_path, key):
#         if key == 1:
#             self.vol.change_dir('..')
#         else:
#             self.vol.change_dir(os.path.basename(folder_path))

#         if os.path.isdir(folder_path):
#             self.folder_path.set(folder_path)
#             self.create_folder_view()
#             self.show_folder_info(folder_path)
#         elif folder_path.lower().endswith('.txt'):
#             self.show_txt_file_content(folder_path)

#     def show_parent_folder(self):
#         parent_folder = os.path.dirname(self.folder_path.get())
#         self.show_folder_contents(parent_folder, 1)

#     def get_folder_file_contents(self, path):
#         items = []
#         try:
#             if path != "":
#                 next_dir = self.vol.visit_dir(path)
#                 record_list = next_dir.get_active_records()
#             else:
#                 record_list = self.dir_tree.get_active_records()
#             for record in record_list:
#                 items.append(record.file_name['long_name'])

#         except FileNotFoundError:
#             pass
#         except PermissionError:
#             pass
#         return items

#     def show_tree(self):
#         self.info_text.delete("1.0", tk.END)

#         cur_path = self.folder_path.get()

#         def draw_tree(entry, prefix="", last=False):
#             self.info_text.insert(tk.END, prefix + ("└── " if last else "├── ") + entry["Name"] + "\n")
#             # check if is archive
#             if entry["Flags"] & 0b100000:
#                 return

#             self.vol.change_dir(entry["Name"])
#             entries = self.vol.get_dir()
#             l = len(entries)
#             for i in range(l):
#                 if entries[i]["Name"] in (".", ".."):
#                     continue
#                 prefix_char = "    " if last else "│   "
#                 draw_tree(entries[i], prefix + prefix_char, i == l - 1)
#             self.vol.change_dir("..")
        
#         try:
#             if cur_path != "":
#                 self.vol.change_dir(cur_path)
#                 self.info_text.insert(tk.END, self.vol.get_cwd() + "\n")
#             else:
#                 self.info_text.insert(tk.END, self.vol.get_cwd() + "\n")
#             entries = self.vol.get_dir()
#             l = len(entries)
#             for i in range(l):
#                 if entries[i]["Name"] in (".", ".."):
#                     continue
#                 draw_tree(entries[i], "", i == l - 1)
#         except Exception as e:
#             self.info_text.insert(tk.END, f"[ERROR] {e}\n")
#         finally:
#             self.vol.change_dir(cur_path)


#     def show_txt_file_content(self, file_path):
#         try:
#             content = self.vol.get_text_content(file_path)

#             txt_window = tk.Toplevel(self)
#             txt_window.title("Text Viewer")

#             txt_frame = ttk.Frame(txt_window)
#             txt_frame.pack(fill="both", expand=True)

#             txt_scrollbar = ttk.Scrollbar(txt_frame, orient="vertical")
#             txt_scrollbar.pack(side="right", fill="y")

#             txt_text = tk.Text(txt_frame, yscrollcommand=txt_scrollbar.set)
#             txt_text.pack(fill="both", expand=True)

#             txt_scrollbar.config(command=txt_text.yview)

#             txt_text.insert(tk.END, content)
#             txt_text.config(state="disabled")
#         except Exception as e:
#             messagebox.showerror("[ERROR]", f"Unable to open the file: {str(e)}")

#     def clear_folder_view(self):
#         for widget in self.folder_view_frame.winfo_children():
#             widget.destroy()


# if __name__ == "__main__":
#     volume_name = 'D:'
#     if FAT32.check_fat32(volume_name):
#         vol = FAT32(volume_name)
#     elif NTFS.is_ntfs(volume_name):
#         vol = NTFS(volume_name)

#     app = FolderExplorer(vol)
#     app.mainloop()


import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Union
from NTFS import NTFS
from FAT32 import FAT32

def is_folder(folder_path):
    drive, path = os.path.splitdrive(folder_path)
    return bool(path and len(path.strip(os.path.sep)) > 0)

class FolderExplorer(tk.Tk):
    def __init__(self, volume: Union[FAT32, NTFS]) -> None:
        super().__init__()
        self.title("Folder Explorer")
        self.geometry("800x600")
        self.configure(bg="light gray")  # Thiết lập màu nền cho cửa sổ

        self.vol = volume
        self.folder_path = tk.StringVar(value=self.vol.get_cwd())

        self.create_widgets()

    def create_widgets(self):
        # Tạo frame chứa đường dẫn
        path_frame = ttk.Frame(self)
        path_frame.pack(fill="x", padx=5, pady=2)

        self.path_entry = ttk.Entry(path_frame, textvariable=self.folder_path, state="readonly")
        self.path_entry.pack(fill="x")

        # Tạo frame chứa các nút điều hướng và hiển thị thông tin
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", padx=5, pady=2)

        self.tree_button = ttk.Button(control_frame, text="Draw Tree", command=self.show_tree)
        self.tree_button.pack(side="left", padx=5, pady=2)

        self.info_button = ttk.Button(control_frame, text="Show Disk Information", command=self.get_drive_info)
        self.info_button.pack(side="left", padx=5, pady=2)

        # Tạo frame chứa khung hiển thị thư mục và thông tin thư mục
        content_frame = ttk.Frame(self)
        content_frame.pack(fill="both", expand=True, padx=5, pady=2)

        # Khung hiển thị thư mục
        self.folder_view_frame = ttk.Frame(content_frame, style="Dir.TFrame")  # Sử dụng style để thiết lập màu nền cho frame hiển thị thư mục
        self.folder_view_frame.pack(side="left", fill="both", expand=True)

        # Khung hiển thị thông tin thư mục
        self.folder_info_frame = ttk.Frame(content_frame, style="Info.TFrame")  # Sử dụng style để thiết lập màu nền cho frame hiển thị thông tin thư mục
        self.folder_info_frame.pack(side="right", fill="both", expand=True)

        self.folder_info_text = tk.Text(self.folder_info_frame, height=10, width=30, background="light gray", foreground="black", font=("Arial", 10))
        self.folder_info_text.pack(fill="both", expand=True)

        self.create_folder_view()

    def get_drive_info(self):
        try:
            info_str = str(self.vol)
            messagebox.showinfo("Disk Information", info_str)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_folder_info(self, folder_path):
        try:
            if is_folder(folder_path):
                file = self.vol.get_folder_file_information(os.path.basename(folder_path))

                flag = file['Flags']
                atts = []

                if flag & 0b1:
                    atts.append('Read-Only')
                if flag & 0b10:
                    atts.append('Hidden')
                if flag & 0b100:
                    atts.append('System')
                if flag & 0b1000:
                    atts.append('Vollable')
                if flag & 0b10000:
                    atts.append('Directory')
                if flag & 0b100000:
                    atts.append('Archive')

                info_text = f"Name: {file['Name']}\n"
                if atts:
                    info_text += f"Attribute: {', '.join(atts)}\n"
                else:
                    info_text += "Attribute: None\n"
                info_text += f"Date Created: {str(file['Date Created'])}\n"
                info_text += f"Date Modified: {str(file['Date Modified'])}\n"
                info_text += f"Total Size: {file['Sector']} sector"
                self.folder_info_text.delete("1.0", tk.END)
                self.folder_info_text.insert(tk.END, info_text)
            else:
                self.folder_info_text.delete("1.0", tk.END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_folder_view(self):
        self.clear_folder_view()

        items = self.get_folder_file_contents(self.folder_path.get())
        for item in items:
            item_path = os.path.join(self.folder_path.get(), item)
            if os.path.isdir(item_path):
                item_button = ttk.Button(self.folder_view_frame, text=item, command=lambda i=item: self.show_folder_contents(os.path.join(self.folder_path.get(), i), 0))
                item_button.pack(side="top", padx=5, pady=2)
            else:
                if item.lower().endswith('.txt'):
                    item_label = ttk.Label(self.folder_view_frame, text=item, foreground="blue", cursor="hand2")
                    item_label.bind("<Button-1>", lambda event, i=item: self.show_txt_file_content(os.path.join(self.folder_path.get(), i)))
                    item_label.pack(side="top", padx=5, pady=2)
                else:
                    item_label = ttk.Label(self.folder_view_frame, text=item, foreground="black", cursor="hand2")
                    item_label.bind("<Button-1>", lambda event: messagebox.showerror("Error", "Only .txt files can be opened"))
                    item_label.pack(side="top", padx=5, pady=2)

        if self.folder_path.get() != os.path.splitdrive(self.folder_path.get())[0] + "\\":
            back_button = ttk.Button(self.folder_view_frame, text="Back", command=self.show_parent_folder, style="Back.TButton")  # Thêm style để định dạng nút Back
            back_button.pack(side="top", padx=5, pady=5)

    def show_folder_contents(self, folder_path, key):
        if key == 1:
            self.vol.change_dir('..')
        else:
            self.vol.change_dir(os.path.basename(folder_path))

        if os.path.isdir(folder_path):
            self.folder_path.set(folder_path)
            self.create_folder_view()
            self.show_folder_info(folder_path)
        elif folder_path.lower().endswith('.txt'):
            self.show_txt_file_content(folder_path)

    def show_parent_folder(self):
        parent_folder = os.path.dirname(self.folder_path.get())
        self.show_folder_contents(parent_folder, 1)

    def get_folder_file_contents(self, path):
        items = []
        try:
            if path != "":
                next_dir = self.vol.visit_dir(path)
                record_list = next_dir.get_active_records()
            else:
                record_list = self.dir_tree.get_active_records()
            for record in record_list:
                items.append(record.file_name['long_name'])

        except FileNotFoundError:
            pass
        except PermissionError:
            pass
        return items

    def show_tree(self):
        self.folder_info_text.delete("1.0", tk.END)

        cur_path = self.folder_path.get()

        def draw_tree(entry, prefix="", last=False):
            self.folder_info_text.insert(tk.END, prefix + ("└── " if last else "├── ") + entry["Name"] + "\n")
            # check if is archive
            if entry["Flags"] & 0b100000:
                return

            self.vol.change_dir(entry["Name"])
            entries = self.vol.get_dir()
            l = len(entries)
            for i in range(l):
                if entries[i]["Name"] in (".", ".."):
                    continue
                prefix_char = "    " if last else "│   "
                draw_tree(entries[i], prefix + prefix_char, i == l - 1)
            self.vol.change_dir("..")
        
        try:
            if cur_path != "":
                self.vol.change_dir(cur_path)
                self.folder_info_text.insert(tk.END, self.vol.get_cwd() + "\n")
            else:
                self.folder_info_text.insert(tk.END, self.vol.get_cwd() + "\n")
            entries = self.vol.get_dir()
            l = len(entries)
            for i in range(l):
                if entries[i]["Name"] in (".", ".."):
                    continue
                draw_tree(entries[i], "", i == l - 1)
        except Exception as e:
            self.folder_info_text.insert(tk.END, f"[ERROR] {e}\n")
        finally:
            self.vol.change_dir(cur_path)

    def show_txt_file_content(self, file_path):
        try:
            content = self.vol.get_text_content(file_path)

            txt_window = tk.Toplevel(self)
            txt_window.title("Text Viewer")

            txt_frame = ttk.Frame(txt_window)
            txt_frame.pack(fill="both", expand=True)

            txt_scrollbar = ttk.Scrollbar(txt_frame, orient="vertical")
            txt_scrollbar.pack(side="right", fill="y")

            txt_text = tk.Text(txt_frame, yscrollcommand=txt_scrollbar.set)
            txt_text.pack(fill="both", expand=True)

            txt_scrollbar.config(command=txt_text.yview)

            txt_text.insert(tk.END, content)
            txt_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("[ERROR]", f"Unable to open the file: {str(e)}")

    def clear_folder_view(self):
        for widget in self.folder_view_frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    volume_name = 'D:'
    if FAT32.check_fat32(volume_name):
        vol = FAT32(volume_name)
    elif NTFS.is_ntfs(volume_name):
        vol = NTFS(volume_name)

    app = FolderExplorer(vol)
    app.mainloop()
