__author__ = "Ernesto"
__email__ = "ernestondieki12@gmail.com"
__version__ = "4.2.2"
__dated__ = "27-06-2022"


# from profiler import profile
import mixer
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from stream import Stream
import pafy
from socket import gethostname, gethostbyname
from threading import Thread
from os import chmod, getpid, listdir, popen, remove
from os.path import expanduser, join, dirname, basename, abspath, splitext, exists, normpath
from shutil import rmtree
from re import split as SPLIT, sub
from subprocess import call, STARTUPINFO, STARTF_USESHOWWINDOW
from stat import S_IREAD, S_IWUSR
from plyer import battery, notification
import sys
from send2trash import send2trash
from random import shuffle
from images import *
from time import sleep, time
from datetime import timedelta
from tkinter import (Tk,
                     Frame,
                     Label,
                     Button,
                     PhotoImage,
                     Menu, DoubleVar,
                     Listbox, Entry,
                     Scrollbar, Toplevel,
                     Canvas, Checkbutton, IntVar)
from tkinter.ttk import Scale, Notebook, Style
# from ttkthemes import ThemedStyle
try:
    from idlelib.tooltip import ToolTip
# for python greater than 3.7
except ImportError:
    from idlelib.tooltip import Hovertip as ToolTip
from tkinter.messagebox import askokcancel, showinfo
from tkinter.filedialog import askopenfilenames, askdirectory
from playX import Counta
from configparser import ConfigParser
import webbrowser

BASE_DIR = dirname(abspath(__file__))


def r_path(relpath):
    """
        Get absolute path
    """

    base_path = getattr(sys, "_MEIPASS", BASE_DIR)
    return join(base_path, relpath)


DATA_DIR = r_path("data")
debug = 0


class Settings():
    __slots__ = ()
    # in seconds
    TIMEOUT = 30
    LISTBOX_OPTIONS = {"bg": "white smoke", "fg": "black", "width": 42,
                       "selectbackground": "DeepSkyBlue3", "selectforeground": "white",
                       "height": 43, "relief": "flat", "font": ("New Times Roman", 9), "highlightthickness": 0}
    SCALE_OPTIONS = {"from_": 0, "orient": "horizontal", "length": 225, "cursor": "hand2"}
    FILENAMES_INITIALDIR = expanduser("~\\Music")


class Player(Settings):
    """
        Plays
        ('.mp3', '.m4a', '.aac', '.mp4',
        '.flac', '.mov', '.mkv', '.flv',
        '.m2v', '.m3u', '.m4v', '.mpeg1',
        '.mpeg2', '.m1v', '.mpeg4', '.part',
        '.3g2', '.avi', '.mpeg', '.mpg',
        '.mp1','.ogg', '.wav', '.3gp',
        '.wmv', '.mod', '.mp2',
        '.wma', '.mka', '.dat'...)
        files in shuffle and repeat mode
        win is tkinter's toplevel widget Tk
    """
    _CONFIG = ConfigParser()
    try:
        _CONFIG.read(DATA_DIR + "\\lazylog.cfg")
        BG = _CONFIG["theme"]["bg"]
        FG = _CONFIG["theme"]["fg"]
    # exceptions; KeyError, ValueError
    except Exception:
        BG = "gray28"
        FG = "gray97"
        try:
            _CONFIG.add_section("theme")
        except Exception:
            pass
        _CONFIG.set("theme", "bg", "gray28")
        _CONFIG.set("theme", "fg", "gray97")

    def __init__(self, win):
        self._root = win
        self._root.resizable(0, 0)
        self._root.config(bg=Player.BG)
        self._root.title("Lazy Selector")
        self._root.tk_focusFollowsMouse()
        self._root.wm_protocol("WM_DELETE_WINDOW", self._kill)
        # use png image for icon
        self._root.wm_iconphoto(1, PhotoImage(data=APP_IMG))
        # for screens with high DPI minus 102
        self._screen_height = self._root.winfo_screenheight() - 104 if self._root.winfo_screenheight() >= 900 else self._root.winfo_screenheight() - 84
        # if debug: print(self._screen_height)

        self.shuffle_mixer = mixer.VLC()
        self.streamer = Stream()
        self._progress_variable = DoubleVar()
        self.FORGET = IntVar()
        try:
            self.FORGET.set(int(Player._CONFIG["theme"]["forget"]))
        # exceptions; KeyError, ValueError
        except Exception:
            self.FORGET.set(0)
            Player._CONFIG.set("theme", "forget", str(self.FORGET.get()))

        try:
            position = Player._CONFIG["window"]["position"]
            self.search_str = Player._CONFIG["files"]["search"]
        except KeyError:
            self.search_str = "official music video"
            position = f"{self._root.winfo_x()}+{self._root.winfo_y()}"
        # initial path to Add to Queue
        self._root.geometry("318x118+" + position)
        self._loaded_files = []
        self._all_files = []
        self.collected = []
        self.index = -1
        self.collection_index = -1
        self.stream_index = -1
        self._start = 0
        self.tab_num = 0
        self.isStreaming = 0
        self.change_stream = 1
        self._title_link = None
        if not self.isOffline:
            self._title_link = self.streamer.search(self.search_str)
        # let duration be greater than 0; prevent slider being at the end on startup
        self.duration = 60
        self._song = ""
        self._title_txt = ""
        self.audio_download_thread = None
        self.video_download_thread = None
        self.ftime = "00:00"
        self._play_btn_command = None
        self._play_prev_command = None
        self._play_next_command = None
        self.list_frame = None
        self.listbox = None
        self.controls_frame = None
        self.main_frame = None
        self.done_frame = None
        self.sort_frame = None
        self.top = None
        self._active_repeat = 0
        self._files_selected = 0
        self._slider_above = 0
        self._playing = 0
        self.reset_preferences = 0
        self._supported_extensions = ('.mp3', '.m4a', '.aac', '.mp4',
                                      '.flac', '.avi', '.wav', '.mkv', '.flv',
                                      '.m2v', '.m3u', '.m4v', '.mpeg1',
                                      '.mpeg2', '.m1v', '.mpeg4', '.part',
                                      '.3g2', '.mpeg', '.mpg',
                                      '.mp1', '.ogg', '.mov', '.3gp',
                                      '.wmv', '.mod', '.mp2',
                                      '.wma', '.mka', '.dat', 'webm',
                                      '.MP3', '.M4A', '.AAC', '.MP4',
                                      '.FLAC', '.AVI', '.WAV', '.MKV', '.FLV',
                                      '.M2V', '.M3U', '.M4V', '.MPEG1',
                                      '.MPEG2', '.M1V', '.MPEG4', '.PART',
                                      '.3G2', '.MPEG', '.MPG',
                                      '.MP1', '.OGG', '.MOV', '.3GP',
                                      '.WMV', '.MOD', '.MP2',
                                      '.WMA', '.MKA', '.DAT', 'WEBM')
        # value to let refresher open dir chooser; otherwise use previous
        self._open_folder = 0
        self.previous_img = PhotoImage(data=PREVIOUS_IMG)
        self.play_img = PhotoImage(data=PLAY_IMG)
        self.pause_img = PhotoImage(data=PAUSE_IMG)
        self.next_img = PhotoImage(data=NEXT_IMG)
        self.lpo_image = PhotoImage(data=LDARKPOINTER_IMG)
        self.play_btn_img = self.play_img
        if Player.BG == "gray97":
            self._repeat_image = PhotoImage(data=REPEAT_IMG)
            self.rpo_image = PhotoImage(data=POINTER_IMG)
        else:
            self._repeat_image = PhotoImage(data=DARKREPEAT_IMG)
            self.rpo_image = PhotoImage(data=DARKPOINTER_IMG)

        self.menubar = Menu(self._root)
        self._root.config(menu=self.menubar)
        self.file_menu = Menu(self.menubar, tearoff=0,
                              fg=Player.FG, bg=Player.BG)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Folder",
                                   command=self._manual_add)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Add to Queue",
                                   command=self._select_fav)

        self.theme_menu = Menu(self.menubar, tearoff=0,
                               fg=Player.FG, bg=Player.BG)
        self.menubar.add_cascade(label="Theme", menu=self.theme_menu)
        self.theme_menu.add_command(label="Light",
                                    command=lambda: self._update_color("gray97", "black"))
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark",
                                    command=lambda: self._update_color("gray28", "gray97"))

        self.about_menu = Menu(self.menubar, tearoff=0,
                               fg=Player.FG, bg=Player.BG)
        self.menubar.add_cascade(label="Help", menu=self.about_menu)
        self.about_menu.add_command(label="Switch Slider", command=self._change_place)
        self.about_menu.add_separator()
        self.about_menu.add_checkbutton(label="Reset preferences", command=self._remove_pref)
        self.about_menu.add_separator()
        self.about_menu.add_command(label="About Lazy Selector", command=self._about)
        self._set_thread(self._set_uptime, "Timer").start()
        # this window will not show but will take less time to show next time
        self._init()
        self._refresher()

        if battery.get_state()["percentage"] < 16:
            notification.notify(title="Lazy Selector",
                                message=f'{battery.get_state()["percentage"]}% Charge Available',
                                app_name="Lazy Selector",
                                timeout=5,
                                app_icon=DATA_DIR + "\\app.ico" if exists(DATA_DIR + "\\app.ico") else None)

# ------------------------------------------------------------------------------------------------------------------------------

    def _on_enter(self, event):
        """
            On mouse over widget
        """

        event.widget["bg"] = "gray97"

    def _on_leave(self, event):
        """
            On mouse leave widget
        """

        if self.controls_frame is not None:
            event.widget["bg"] = "gray28"
        else:
            # use the current theme on leave; that includes light
            event.widget["bg"] = Player.BG

    def _convert(self, text):
        """
            Trims title text
        """

        if len(text) > 47:  # not so perfect
            text = text[:44] + "..."

        return text

    @property
    def isOffline(self) -> bool:
        return gethostbyname(gethostname()) == "127.0.0.1"

# ------------------------------------------------------------------------------------------------------------------------------

    def _update_bindings(self):
        """
            Mouse hover bindings; to change background of button in dark mode
        """

        if self.controls_frame is not None or Player.BG == "gray28":
            self._previous_btn.bind("<Enter>", self._on_enter)
            self._previous_btn.bind("<Leave>", self._on_leave)
            self._play_btn.bind("<Enter>", self._on_enter)
            self._play_btn.bind("<Leave>", self._on_leave)
            self._next_btn.bind("<Enter>", self._on_enter)
            self._next_btn.bind("<Leave>", self._on_leave)

# ------------------------------------------------------------------------------------------------------------------------------

    def __update_listbox(self):
        """
            Inserts items to the Listbox
        """

        self.listbox.pack_forget()
        self.scrollbar.pack_forget()
        self.searchlabel.configure(text="Updating...")
        self.searchlabel.place(x=10, y=72)
        self.collection_index = -1
        self.collected = []
        self.searchbar.delete(0, "end")
        self.listbox.delete(0, "end")
        try:
            self.back_toplaylist_btn.destroy()
        except AttributeError:
            pass
        try:
            # self._root.geometry("318x118+")
            for file in self._all_files:

                try:
                    self.listbox.insert("end", file.encode("utf-8"))
                except Exception:
                    continue
            self.listbox.selection_set(self.index)
            self.listbox.see(self.index)
            self.listbox.activate(self.index)
            self.listbox.pack(side="left", padx=3)
            self.scrollbar.pack(side="left", fill="y")
            self._resize_listbox()
        except AttributeError:
            pass

    def _update_listbox(self):
        """
            Threads __update_listbox function
            Inserts items to listbox from self._all_files
        """

        if self.listbox is not None and self.scrollbar is not None:
            self._set_thread(self.__update_listbox, "Update Listbox").start()

# ------------------------------------------------------------------------------------------------------------------------------

    def _resize_listbox(self):
        """
            Dynamically resize Listbox according to the number of items
        """

        self.searchbar.place(x=178, y=73)
        if self.listbox.size() > 35:
            self._root.geometry(f"318x{self._screen_height}+" + f"{self._root.winfo_x()}+{5}")
            if not self.tab_num:
                self.searchlabel.configure(text="Search:")
            else:
                self.searchlabel.configure(text="Search online:")
        elif self.listbox.size() > 0:
            # one line takes 16 pixels on my machine
            height = 124 + (self.listbox.size() * 16)
            y = self._root.winfo_y()
            # if debug: print("Listbox Height:", height, "Items:", self.listbox.size())
            difference = self._screen_height - (y + height)
            # if the new height surpasses screen bottom, then subtract the difference from y to get new y
            if difference < 0:
                y = y - (difference * -1)
                if y < 5:  # prevent the window from going beyond the screen top
                    y = 5
            self._root.geometry(f"318x{height}+" + f"{self._root.winfo_x()}+{y}")
            if not self.tab_num:
                self.searchlabel.configure(text="Search:")
            else:
                self.searchlabel.configure(text="Search online:")
        else:
            self._root.geometry(f"318x{self._screen_height}+" + f"{self._root.winfo_x()}+{5}")
            self.searchlabel.configure(text="No files found!")

# ------------------------------------------------------------------------------------------------------------------------------

    def __on_search(self):
        """
            updates listbox with match for string searched else updates listbox
            fetches and updates online streams if tab_num is 1
        """
        self.search_str = self.searchbar.get()
        if self.tab_num:
            # online stream tab
            if len(self.search_str) > 1 and not self.isOffline:
                self.searchlabel.configure(text="Updating...")
                # do search here bacause;
                # this function is threaded,
                # query_str is needed; unlike _handle_stream_tab's search
                self._title_link = self.streamer.search(self.search_str)
                # update listview window in streams tab
                self.thread_updating_streams()
                self.searchlabel.configure(text="Search online:")
                self.stream_index = -1
        else:
            # local files tab
            # if debug: print("Searched:", searchstr)
            self.collected = []
            self.collection_index = -1
            if len(self.search_str) > 1:
                try:
                    self.back_toplaylist_btn.destroy()
                except AttributeError:
                    pass
                # ---------------------------------back button-------------
                self.back_toplaylist_btn = Button(self.controls_frame, image=self.lpo_image, bg="gray28", anchor="w",
                                                  pady=0, relief="flat", width=50, height=16)
                self.back_toplaylist_btn.place(x=1, y=70)
                search_string = self.search_str.lower()
                # ---------------------------------
                self.listbox.delete(0, "end")
                for song in self._all_files:
                    if search_string in song.lower():
                        try:
                            self.listbox.insert("end", song.encode("utf-8"))
                        except Exception:
                            continue
                        self.collected.append(song)
                self._resize_listbox()
                # give the button functionality after update is done
                self.back_toplaylist_btn.configure(command=self._update_listbox)
            else:
                if self.listbox.size() != len(self._all_files):
                    self._update_listbox()

    def _on_search(self, event):
        """
            Threads __on_search function
        """

        self._set_thread(self.__on_search, "Search").start()

# ------------------------------------------------------------------------------------------------------------------------------

    def _on_refresh(self):

        self.index = -1
        all_files = listdir(self._songspath)
        self._all_files = [i for i in all_files if i.endswith(self._supported_extensions)]
        shuffle(self._all_files)
        self._all_files.sort(key=self.counta.get_freq)

# ------------------------------------------------------------------------------------------------------------------------------

    def _delete_listitem(self):
        """
            Listbox's Remove from List
        """

        # if debug: print(len(self._all_files))
        for i in self.listbox.curselection()[::-1]:
            if len(self.collected) == 0:
                item = self._all_files[i]
            else:
                item = self.collected[i]
            try:
                self._all_files.remove(item)
            except ValueError:
                pass
            if item in self.collected:
                self.collected.remove(item)
            self.listbox.delete(i)
            # if debug: print(i, item)
            if i < self.index:
                # adjust to playlist shifting
                self.index -= 1
        self._resize_listbox()
        # if debug: print(len(self._all_files))

# ------------------------------------------------------------------------------------------------------------------------------

    def _remove_streams(self):
        """ remove selected streams from view """
        for i in self.listview.curselection()[::-1]:
            title = self.listview.get(i)
            self._title_link.pop(title)
            self.listview.delete(i)

# ------------------------------------------------------------------------------------------------------------------------------

    def _send2trash(self):
        """
            Try sending to trash if not removable disk, else delete permanently
        """

        # if debug: print(len(self._all_files))
        if askokcancel("Lazy Selector", "Selected files will be deleted from storage\nContinue to delete?"):
            for i in self.listbox.curselection()[::-1]:
                if len(self.collected) == 0:
                    item = self._all_files[i]
                else:
                    item = self.collected[i]
                try:
                    self._all_files.remove(item)
                except ValueError:
                    pass
                if item in self.collected:
                    self.collected.remove(item)
                    self.delete_safe(join(self._songspath, item))
                self.listbox.delete(i)
                # delete file
                filename = join(normpath(self._songspath), item)
                try:
                    send2trash(filename)
                except Exception:
                    self.delete_safe(filename)
                # if debug: print(i, item)
                if i < self.index:
                    # adjust to playlist shifting
                    self.index -= 1
            self._resize_listbox()
            # if debug: print(len(self._all_files))

# ------------------------------------------------------------------------------------------------------------------------------

    def _addto_queue(self):
        """
            Listbox's Play Next
        """
        try:
            i = self.listbox.curselection()[-1]

            if len(self.collected) == 0 and (i != self.index and i != self.index + 1):  # if adding from main list
                item = self._all_files[i]

                try:
                    if i > self.index:
                        # if the selected item is below the currently, delete first to avoid shift in indexes
                        # deleting after insertion shifts the item down by 1
                        self.listbox.delete(i)
                        self._all_files.remove(self._all_files[i])  # remove item
                        self.listbox.insert(self.index + 1, item)
                        self._all_files.insert(self.index + 1, item)
                    else:
                        # insert first then delete before items shift up, including the currently playing
                        self.listbox.insert(self.index + 1, item)
                        self._all_files.insert(self.index + 1, item)
                        self.listbox.delete(i)
                        self._all_files.remove(self._all_files[i])  # remove item
                        self.index -= 1
                except ValueError:
                    pass

                if self.shuffle_mixer.state.value == 0 and not self._playing:  # if player hasn't started
                    self.listbox.selection_set(0)
                    self._on_click()
                self.listbox.selection_clear(0, "end")
                self.listbox.selection_set(self.index)
                self.listbox.activate(self.index)
            elif (len(self.collected) != 0) and (i != self.collection_index
                                                 and i != self.collection_index + 1) and self.collection_index != -1:  # if adding from searched list
                item = self.collected[i]
                try:
                    if i > self.collection_index:
                        # delete first then insert for index greater than pivot (collection_index)
                        self.listbox.delete(i)
                        self.collected.remove(self.collected[i])  # remove item
                        self.listbox.insert(self.collection_index + 1, item)
                        self.collected.insert(self.collection_index + 1, item)
                    else:
                        # if index to add is less than the pivot
                        self.listbox.insert(self.collection_index + 1, item)
                        self.collected.insert(self.collection_index + 1, item)
                        self.listbox.delete(i)
                        self.collected.remove(self.collected[i])  # remove item
                        self.collection_index -= 1
                except ValueError:
                    pass
                self.listbox.selection_clear(0, "end")
                self.listbox.selection_set(self.collection_index)
                self.listbox.activate(self.collection_index)
                # if debug: print(self.collection_index)
        except IndexError:  # IndexError occurs when nothing was selected in the Listbox
            pass

    def _addto_playlist(self):

        i = self.listbox.curselection()[-1]
        self.listbox.selection_clear(0, "end")
        item = self.collected[i]
        num = self._all_files.index(item)
        # if item selected is above the currently playing in the playlist
        if num < self.index:
            # move 1 index up
            # since we're removing before inserting
            # removing an item at an index less than self.index
            # causes list to shift by -1
            # so our true index becomes self.index - 1
            self.index = self.index - 1
        if item != self._all_files[self.index + 1]:
            try:
                self._all_files.remove(item)  # remove and insert later
            except ValueError:
                pass
            self._all_files.insert(self.index + 1, item)

# ------------------------------------------------------------------------------------------------------------------------------

    def _listbox_rightclick(self, event):
        """
            Popup event function to bind to local files' listbox right click
        """

        popup = Menu(self.listbox, tearoff=0, bg="gray28", fg="gray97", font=("New Times Roman", 9, "bold"),
                     activebackground="DeepSkyBlue3")
        popup.add_command(label="Play", command=self._on_click)
        if len(self.collected) != 0:
            popup.add_command(label="Play Next Here", command=self._addto_queue)
            popup.add_separator()
            popup.add_command(label="Play Next in Playlist", command=self._addto_playlist)
        else:
            popup.add_command(label="Play Next", command=self._addto_queue)
            popup.add_separator()
        popup.add_command(label="Remove from Playlist", command=self._delete_listitem)
        popup.add_separator()
        popup.add_command(label="Delete from Storage", command=self._send2trash)
        try:
            popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            popup.grab_release()

    def _rightclick(self, event):
        """
            Popup event function to bind to main window right click
        """

        popup = Menu(self.main_frame, tearoff=0, bg=Player.BG, fg=Player.FG, font=("New Times Roman", 9),
                     activebackground="DeepSkyBlue3")
        popup.add_command(label="Show Playlist", command=self._listview)
        popup.add_command(label="Add to Queue", command=self._select_fav)
        popup.add_separator()
        popup.add_command(label="Refresh Playlist", command=self._on_refresh)
        try:
            popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            popup.grab_release()

# ------------------------------------------------------------------------------------------------------------------------------
    def _streams_rightclick(self, event):
        """
            Popup event function to bind to streams listbox right click
        """

        popup = Menu(self.listview, tearoff=0, bg="gray28", fg="gray97", font=("New Times Roman", 9, "bold"),
                     activebackground="DeepSkyBlue3")
        popup.add_command(label="Play", command=self._on_click)
        popup.add_separator()
        popup.add_command(label="Download Audio", command=self.download_audio)
        popup.add_command(label="Download Video", command=self.download_video)
        popup.add_separator()
        popup.add_command(label="Remove from Playlist", command=self._remove_streams)
        try:
            popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            popup.grab_release()
# ------------------------------------------------------------------------------------------------------------------------------

    def scroll_widget(self, event):
        """
            Event function to bind to mouse wheel
        """

        event.widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
# ----------------------------------------------------------------------------------------------------------------------

    def _download_audio(self):
        """ download youtube audio of link """
        # get link from title
        title = self.listview.selection_get()
        link = self._title_link.get(title)

        try:
            if not self._playing:
                self.shuffle_mixer.prevent_sleep()
            video = pafy.new(link)  # ydl_opts={"writethumbnail": True}
            best_audio = video.getbestaudio(preftype="mp3", ftypestrict=False)
            # replace the characters in [] in title, because filenames can't contain them
            save_title = sub(r'[:\\/"*?|<>]', "-", video.title)
            temp_filename = join(self._songspath, f"{save_title}.{best_audio.extension}")
            path, ext = splitext(temp_filename)
            output_filename = f"{path}.mp3"
            if not exists(output_filename):

                best_audio.download(filepath=temp_filename, quiet=True, callback=self.download_callback)
                # convert to mp3
                self.status_bar.configure(text="Converting to MP3 audio...")

                if ext.lower() != ".mp3":
                    audio = AudioFileClip(temp_filename)
                    audio.write_audiofile(output_filename, logger=None)
                    # delete temp_filename when done if initial ext != mp3
                    self.delete_safe(temp_filename)
                # done converting
                self._all_files.append(basename(output_filename))
            self.status_bar.configure(text=f"Downloaded to '{basename(self._songspath)}' folder")
        except Exception:
            self.status_bar.configure(text="An error occured...")
        self.audio_download_thread = None
        if not self._playing:
            self.shuffle_mixer.release_sleep()

    def download_audio(self):
        """ threaded download audio """
        if self.audio_download_thread is None and self.video_download_thread is None:
            self.type_downloading = "Audio"
            self.audio_download_thread = self._set_thread(self._download_audio, "audio_download")
            self.audio_download_thread.start()

    def _download_video(self):
        """ download youtube video of link """
        # get link from title
        title = self.listview.selection_get()
        link = self._title_link.get(title)

        try:
            if not self._playing:
                self.shuffle_mixer.prevent_sleep()
            video = pafy.new(link)
            best_video = video.getbest(preftype="mp4", ftypestrict=False)
            # replace the characters in [] with -, because filenames can't contain them
            save_title = sub(r'[:\\/"*?|<>]', "-", video.title)
            temp_filename = join(self._songspath, f"{save_title}.{best_video.extension}")
            path, ext = splitext(temp_filename)
            output_filename = f"{path}.mp4"
            if not exists(output_filename):

                best_video.download(filepath=temp_filename, quiet=True, callback=self.download_callback)
                # convert to mp4
                self.status_bar.configure(text="Converting to MP4 video...")

                if ext.lower() != ".mp4":
                    video = VideoFileClip(temp_filename)
                    video.write_videofile(output_filename, threads=2, logger=None)
                    # delete temp_filename when done if ext != mp4
                    self.delete_safe(temp_filename)
                # done converting
                self._all_files.append(basename(output_filename))
            self.status_bar.configure(text=f"Downloaded to '{basename(self._songspath)}' folder")
        except Exception:
            self.status_bar.configure(text="An error occured...")
        self.video_download_thread = None
        if not self._playing:
            self.shuffle_mixer.release_sleep()

    def download_video(self):
        """ threaded download video """
        if self.video_download_thread is None and self.audio_download_thread is None:
            self.type_downloading = "Video"
            self.video_download_thread = self._set_thread(self._download_video, "video_download")
            self.video_download_thread.start()

    def download_callback(self, total, received, ratio, rate, eta):
        """ called for every bytes received """
        readable = round(total / 1048576, 2)
        self.status_bar.configure(text=f"{self.type_downloading} downloaded: {round(ratio * 100, 2)}% of {readable} MB")

    def delete_safe(self, filename: str):
        try:
            remove(filename)
        except Exception:
            pass

# ----------------------------------------------------------------------------------------------------------------------

    def _which_tab(self, event):
        """
            Event function to bind to notebook
            gets the tab number
        """

        self.tab_num = int(event.widget.index("current"))
        if self.tab_num:
            self.searchlabel.configure(text="Search online:")
            ToolTip(self.searchbar, "Type key words and\nPress 'enter' to search")
            self._root.geometry(f"318x{self._screen_height}+" + f"{self._root.winfo_x()}+{5}")
        else:
            # local files tab
            self.searchlabel.configure(text="Search:")
            ToolTip(self.searchbar, "Press 'enter' to search")
            self._resize_listbox()

# ----------------------------------------------------------------------------------------------------------------------
    # @profile
    def _init(self):
        """
            Main window
            Called from self.controls_frame or from self.sort_frame
            or after self.done_frame is set to None
        """

        if self.main_frame is not None:
            self.main_frame.pack_forget()
            self.main_frame = None
        elif self.sort_frame is not None:
            self.sort_frame.pack_forget()
            self.sort_frame = None
        try:
            self.controls_frame.pack_forget()
            self.list_frame.pack_forget()
            self.listbox.pack_forget()
            self.scrollbar.pack_forget()
            self.controls_frame, self.list_frame = None, None
            self.listbox, self.scrollbar = None, None
            self.progress_bar.style = None
            self.collected = []
            self.tab_num = 0
            self.controls_frame = None
        except AttributeError:
            pass
        self._root.geometry("318x118")
        self._root.config(bg=Player.BG)
        self.main_frame = Frame(self._root, bg=Player.BG, width=318, height=118)
        self.main_frame.pack()
        self.main_frame.bind("<Button-2>", self._rightclick)
        self.main_frame.bind("<Button-3>", self._rightclick)
        self.progress_bar = Scale(self.main_frame, command=self._slide, to=int(self.duration),
                                  variable=self._progress_variable, **self.SCALE_OPTIONS)

        self.current_time_label = Label(self.main_frame, padx=0, text=self.ftime, width=7, anchor="e",
                                        bg=Player.BG, font=('arial', 9, 'bold'), fg=Player.FG)
        # ----------------------------------------------------------------------------------------------------------------------

        self._title = Label(self.main_frame, pady=0, bg=Player.BG,
                            text=self._title_txt, width=44, height=1,
                            font=('arial', 8, 'bold'), fg=Player.FG, anchor="w")
        self._title.place(x=26, y=1)
        self.playlist_btn = Button(self.main_frame, relief="flat", image=self.rpo_image,
                                   height=15, pady=0, padx=0, bg=Player.BG, command=self._listview)
        self.playlist_btn.place(x=1, y=1)
        # ---------------------------------------------------------------------------------------------

        self._shuffle = Button(self.main_frame, command=self.on_eos, text="SHUFFLE", padx=8,
                               bg=Player.BG, fg=Player.FG, font=("arial", 15, "bold"), relief="groove")
        self._shuffle.place(x=97, y=23)

        self._previous_btn = Button(self.main_frame, padx=0, bg=Player.BG, fg=Player.FG,
                                    command=self._play_prev_command, image=self.previous_img,
                                    font=("arial", 7, "bold"), relief="groove")

        self._play_btn = Button(self.main_frame, padx=0, bg=Player.BG,
                                command=self._play_btn_command, image=self.play_btn_img,
                                fg=Player.FG, font=("arial", 7, "bold"), relief="groove")

        self._next_btn = Button(self.main_frame, padx=0, bg=Player.BG,
                                command=self._play_next_command, image=self.next_img,
                                fg=Player.FG, font=("arial", 7, "bold"), relief="groove")

        self._repeat_btn = Button(self.main_frame, pady=0, padx=0, bg=Player.BG, width=20,
                                  command=self._onoff_repeat, height=15,
                                  relief="flat", font=("arial", 6, "bold"), anchor="w")

        self.progress_bar.style = Style()
        self.progress_bar.style.theme_use("clam")
        # self.progress_bar.place(x=54, y=98)
        self.check_theme_mode()
        self._repeat_btn.configure(image=self._repeat_image)
        self._update_theme()
        # get online streams after the window has loaded

# ------------------------------------------------------------------------------------------------------------------------------

    def _listview(self):
        """
            Listbox window
            Must be called only from or after self.main_frame
        """
        if self._active_repeat:
            self.image = PhotoImage(data=DARKREPEAT_IMG)
        else:
            self.image = PhotoImage(data=DARKSHUFFLE_IMG)
        if self.main_frame is not None:
            self.main_frame.pack_forget()
            self.main_frame = None
        self._root.config(bg="white smoke")
        self.progress_bar.style = None
        self.controls_frame = Frame(self._root, bg="gray28", width=310, height=94)
        self.controls_frame.pack(fill="both", pady=0)
        # ----------------------------------------------------------------------------------------------------------------------

        self._title = Label(self.controls_frame, pady=0, bg="gray28",
                            text=self._title_txt, width=44, height=1,
                            font=('arial', 8, 'bold'), fg="white", anchor="w")
        self._title.place(x=26, y=1)
        self.playlist_btn = Button(self.controls_frame, relief="flat", image=self.lpo_image,
                                   height=15, pady=0, padx=0, bg="gray28", command=self._init)
        self.playlist_btn.place(x=1, y=1)
        # ---------------------------------------------------------------------------------------------------
        self.current_time_label = Label(self.controls_frame, padx=0, text=self.ftime, width=7, anchor="e",
                                        bg="gray28", font=('arial', 9, 'bold'), fg="white")
        self.current_time_label.place(x=30, y=25)

        self._previous_btn = Button(self.controls_frame, padx=0, bg="gray28", fg="white",
                                    command=self._play_prev_command, image=self.previous_img,
                                    font=("arial", 7, "bold"), relief="groove")
        self._previous_btn.place(x=100, y=25)

        self._play_btn = Button(self.controls_frame, padx=0, bg="gray28", image=self.play_btn_img,
                                command=self._play_btn_command,
                                fg="white", font=("arial", 7, "bold"), relief="groove")
        self._play_btn.place(x=150, y=25)

        self._next_btn = Button(self.controls_frame, padx=0, bg="gray28",
                                command=self._play_next_command, image=self.next_img,
                                fg="white", font=("arial", 7, "bold"), relief="groove")
        self._next_btn.place(x=200, y=25)

        self._repeat_btn = Button(self.controls_frame, bg="gray28", image=self.image,
                                  command=self._onoff_repeat, width=20, height=15, pady=0,
                                  relief="flat", font=("arial", 6, "bold"), anchor="w", padx=0,)
        self._repeat_btn.place(x=245, y=27)

        self.progress_bar = Scale(self.controls_frame, command=self._slide, to=int(self.duration),
                                  variable=self._progress_variable, **self.SCALE_OPTIONS)
        self.progress_bar.style = Style()
        self.progress_bar.style.theme_use("clam")
        self.progress_bar.place(x=46, y=55)

        self.searchlabel = Label(self.controls_frame, font=('arial', 8, 'bold'), text="Search:",
                                 bg="gray28", fg="white", anchor="e", width=23)

        self.searchbar = Entry(self.controls_frame, relief="flat", bg="gray40", fg="white",
                               insertbackground="white")
        self.searchbar.bind("<Return>", self._on_search)
        # self.searchbar.bind("<Control-f>", self._on_click)

        # root for notebook
        self.list_frame = Frame(self._root)
        self.list_frame.pack(fill="both", padx=0, pady=0)
        book = Notebook(self.list_frame)
        notebook_style = Style()
        # make the color of dots around a tab same as background
        notebook_style.configure("TNotebook.Tab", font=("", 8, "bold"), focuscolor="white smoke",
                                 foreground="gray60", background="gray28")
        # make the notebook color light
        notebook_style.configure("TNotebook", background="gray28")
        # make bg and fg white smoke and black respectively when selected
        notebook_style.map("TNotebook.Tab", foreground=(("selected", "black"),),
                           background=(("selected", "white smoke"),), font=(("selected", ("", 9, "bold")),))

        # creating frames for grouping other widgets
        self.local_listview = Frame(book, bg="white smoke")
        self.streams_listview = Frame(book, bg="white smoke")
        # adding tabs
        book.add(self.local_listview, text="Local files")
        book.add(self.streams_listview, text="Online streams")
        book.bind("<ButtonRelease-1>", self._which_tab)
        book.pack(fill="both")

        # creating widgets in tabbed frames
        self.listbox = Listbox(self.local_listview, selectmode="extended", **self.LISTBOX_OPTIONS)
        self.scrollbar = Scrollbar(self.local_listview, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        self.listbox.bind("<Double-Button-1>", self._on_click)
        self.listbox.bind("<Button-2>", self._listbox_rightclick)
        self.listbox.bind("<Button-3>", self._listbox_rightclick)
        self.listbox.bind("<MouseWheel>", self.scroll_widget)
        self.listbox.bind("<Return>", self._on_click)

        self._update_listbox()
        self._update_bindings()
        self.thread_updating_streams()
        if self._active_repeat:
            ToolTip(self._repeat_btn, "Repeat")
        else:
            ToolTip(self._repeat_btn, "Shuffle")
        if self._playing:
            self.duration_tip = ToolTip(self.progress_bar, f"Duration: {timedelta(seconds=self.duration)}")
        ToolTip(self.searchbar, "Press 'enter' to search")
        if self.isStreaming:
            book.select(1)
            book.event_generate("<ButtonRelease-1>")
        # set search input focused
        self.searchbar.focus_set()

# ------------------------------------------------------------------------------------------------------------------------------
    def _handle_stream_tab(self):
        """
            place widgets on streams tab; call after _title_link's been updated
            try connecting and updating streams
        """

        try:
            self.notification.destroy()
            self.reload_button.destroy()
        except AttributeError:
            pass
        try:
            self.listview.destroy()
            self.stream_scrollbar.destroy()
        except AttributeError:
            pass
        self.notification = Label(self.streams_listview,
                                  bg="gray28", fg="white smoke",
                                  text="Fetching...")
        self.notification.pack(padx=30, pady=50)
        # if localhost, no connection
        if self.isOffline and self._title_link is None:
            # create offline widgets
            self.notification.configure(text="No internet connection")
            self.reload_button = Button(self.streams_listview, text="Refresh", font=("", 8, "underline"),
                                        bg="gray28", fg="white smoke", padx=5, pady=3, command=self.thread_updating_streams)
            self.reload_button.pack(padx=40, pady=1)

        # create listbox; scrollbar and try adding data
        else:
            # if no results to display; try getting it again
            if self._title_link is None:
                self._title_link = self.streamer.search(self.search_str)

            self.listview = Listbox(self.streams_listview, **self.LISTBOX_OPTIONS)
            self.stream_scrollbar = Scrollbar(self.streams_listview, command=self.listview.yview)
            self.listview.config(yscrollcommand=self.stream_scrollbar.set)

            self.listview.bind("<Double-Button-1>", self._on_click)
            self.listview.bind("<MouseWheel>", self.scroll_widget)
            self.listview.bind("<Button-2>", self._streams_rightclick)
            self.listview.bind("<Button-3>", self._streams_rightclick)
            self.listview.bind("<Return>", self._on_click)
            try:
                self.status_bar.destroy()
            except AttributeError:
                pass
            # status bar
            self.status_bar = Label(self.streams_listview, anchor="e", font=("", 9, "bold"))
            self.status_bar.pack(fill="x")
            if self._title_link is not None:
                for item in self._title_link.keys():
                    try:
                        self.listview.insert("end", item)
                    except Exception:
                        continue
                self.listview.selection_set(self.stream_index)
                self.listview.see(self.stream_index)
                self.listview.activate(self.stream_index)
                # when done searching and updating listbox
                # if reload_button was previously packed due to no connection
                try:
                    self.reload_button.pack_forget()
                # there's been internet connection from startup; no reload_button
                except AttributeError:
                    pass
                self.notification.pack_forget()
                # map the listbox and its scrollbar
                self.listview.pack(side="left", padx=3)
                self.stream_scrollbar.pack(side="left", fill="y")
            # if still no results to display
            else:
                self.notification.configure(text="Oops! Connected, no internet")
                self.reload_button = Button(self.streams_listview, text="Refresh", font=("", 8, "underline"),
                                            bg="gray28", fg="white smoke", padx=5, pady=3, command=self.thread_updating_streams)
                self.reload_button.pack(padx=40, pady=1)

# ------------------------------------------------------------------------------------------------------------------------------
    def thread_updating_streams(self):
        self._set_thread(self._handle_stream_tab, "stream_tab").start()

# ------------------------------------------------------------------------------------------------------------------------------

    def _on_eop(self):
        """
            Done window
            Responsible for end of player dir chooser
        """

        if self.sort_frame is not None:
            self.sort_frame.pack_forget()
            self.sort_frame = None
        if self.controls_frame is not None:
            self.controls_frame.pack_forget()
            self.list_frame.pack_forget()
            self.listbox.pack_forget()
            self.scrollbar.pack_forget()
            self.controls_frame, self.list_frame = None, None
            self.listbox, self.scrollbar = None, None
            self.progress_bar.style = None
            self.controls_frame = None
            self.tab_num = 0
            self._playing = 0
        elif self.main_frame is not None:
            self.main_frame.pack_forget()
            self.main_frame = None
        self._root.geometry("318x118")
        self._root.config(bg="gray94")
        self.done_frame = Frame(self._root, bg="gray94", width=310, height=118)
        self.done_frame.pack(padx=3, pady=5)
        self.repeat_folder_img = PhotoImage(data=REPEATFOLDER_IMG)
        self.add_folder_img = PhotoImage(data=ADDFOLDER_IMG)

        description = Label(self.done_frame, bg="gray94", width=300,
                            text="  Play Again                 Add New Folder")
        description.pack(side="top", pady=10)
        self.repeat_folder = Button(self.done_frame, image=self.repeat_folder_img,
                                    command=self._repeat_ended, relief="flat")
        self.repeat_folder.pack(padx=70, pady=0, side="left")
        self.add_folder = Button(self.done_frame, image=self.add_folder_img,
                                 command=self._manual_add, relief="flat")
        self.add_folder.pack(padx=0, pady=0, side="left")

# ------------------------------------------------------------------------------------------------------------------------------

    def _on_sort(self):

        if self.sort_frame is not None:
            self.sort_frame.pack_forget()
            self.sort_frame = None
        if self.controls_frame is not None:
            self.controls_frame.pack_forget()
            self.list_frame.pack_forget()
            self.listbox.pack_forget()
            self.scrollbar.pack_forget()
            self.controls_frame, self.list_frame = None, None
            self.listbox, self.scrollbar = None, None
            self.progress_bar.style = None
            self.tab_num = 0
        elif self.main_frame is not None:
            self.main_frame.pack_forget()
            self.main_frame = None
        elif self.done_frame is not None:
            self.done_frame.pack_forget()
            self.done_frame = None
        color = "gray90"
        self._root.geometry("318x118")
        self._root.config(bg=color)
        self.sort_frame = Frame(self._root, bg=color, width=310, height=118)
        self.sort_frame.pack(padx=3, pady=5)
        dsp = Label(self.sort_frame, bg=color, font=("New Times Roman", 9, "bold"),
                    text="Type artist names or songs that should play first\n(separate words by space)")
        dsp.place(x=18, y=5)

        cancel_btn = Button(self.sort_frame, text="Cancel", bg=color, anchor="center", command=self._init)
        cancel_btn.place(x=18, y=80)
        ToolTip(cancel_btn, "Use default shuffle")
        check_btn = Checkbutton(self.sort_frame, bg=color, text="Don't show this again", onvalue=1, offvalue=0, variable=self.FORGET)
        check_btn.place(x=77, y=79)
        ok_btn = Button(self.sort_frame, text="OK", bg=color, command=self._sort_by_keys, padx=10, pady=1, anchor="center")
        ok_btn.place(x=237, y=80)

        label1 = Label(self.sort_frame, bg=color, text="Keywords:",
                       font=("New Times Roman", 9, "bold"), anchor="e")
        label1.place(x=25, y=50)
        self.keywords_shelf = Entry(self.sort_frame, bg="gray94", relief="groove", width=30)
        self.keywords_shelf.place(x=98, y=52)
        self.keywords_shelf.bind("<Return>", self._sort_by_keys)

# ------------------------------------------------------------------------------------------------------------------------------

    def __on_click(self):
        """
            Plays songs clicked from listbox directly
            Tries to mimic on_eos functionalities
        """
        change = 0
        try:
            if self.tab_num:
                if not self.isOffline:
                    self.searchlabel.configure(text="Fetching audio...")
                    # get link from title
                    title = self.listview.selection_get()
                    link = self._title_link.get(title)
                    stream_link = pafy.new(link, basic=False)
                    self._song = stream_link.getbestaudio().url
                    # length in seconds
                    self.duration = stream_link.length
                    self._title_txt = self._convert(title)
                    self.progress_bar["to"] = int(self.duration)
                    self.isStreaming = 1
                    self.stream_index = self.listview.curselection()[-1]
                    self.searchlabel.configure(text="Search online:")
                    change = 1
                else:
                    self.searchlabel.configure(text="Search online:")
                    self._title_link = None
                    self.thread_updating_streams()
            else:
                index = self.listbox.curselection()[-1]
                if len(self.collected) == 0:
                    self._song = join(self._songspath, self._all_files[index])
                    self.index = index
                else:
                    self._song = join(self._songspath, self.collected[index])
                    self.collection_index = index
                self.isStreaming = 0
                change = 1
            if change:
                # if debug: print("Index:", self.collection_index, self._song)
                self._mixer(self._song).play()
                # wait for media meta to be parsed
                self._set_thread(self._updating, "Helper").start()
                self.play_btn_img = self.pause_img
                self._play_btn.configure(image=self.play_btn_img)
        except Exception:
            # Slow internet may cause problems, going offline after connection
            if self.tab_num:
                self.searchlabel.configure(text="Search online:")
            else:
                self.searchlabel.configure(text="Search:")
            self._title_link = None
            self.thread_updating_streams()

# ------------------------------------------------------------------------------------------------------------------------------

    def _on_click(self, event=None):
        """Threads __on_click"""
        try:
            if not self.play_oc.is_alive():
                self.change_stream = 0
                self.play_oc = self._set_thread(self.__on_click, "play_oc")
                self.play_oc.start()
        # if self.play_oc is not defined; define it
        except AttributeError:
            self.change_stream = 0
            self.play_oc = self._set_thread(self.__on_click, "play_oc")
            self.play_oc.start()

# ------------------------------------------------------------------------------------------------------------------------------

    def _change_place(self):
        """
            Switches slider to above or below
        """

        if self.main_frame is not None:
            if self._slider_above:
                timeandbtn = 94
                pb = 98
                controls = 68
            else:
                timeandbtn = 66
                pb = 70
                controls = 86
            self.progress_bar.place(x=54, y=pb)
            self.current_time_label.place(x=0, y=timeandbtn)
            self._previous_btn.place(x=115, y=controls)
            self._play_btn.place(x=145, y=controls)
            self._next_btn.place(x=175, y=controls)
            self._repeat_btn.place(x=280, y=timeandbtn)
            self._root.update_idletasks()
            self._slider_above = not self._slider_above

# ------------------------------------------------------------------------------------------------------------------------------

    def _update_theme(self):
        """
            Updates slider according to the color chosen
            Places widgets in their correct positions
        """

        if self._slider_above:
            timeandbtn = 66
            pb = 70
            controls = 86
        else:
            timeandbtn = 94
            pb = 98
            controls = 68
        if Player.BG == "gray28":
            # make bg color change on hover
            self._update_bindings()
        # Restore slider to previous position
        self._previous_btn.place(x=115, y=controls)
        self._play_btn.place(x=145, y=controls)
        self._next_btn.place(x=175, y=controls)
        self.current_time_label.place(x=0, y=timeandbtn)
        self._repeat_btn.place(x=280, y=timeandbtn)
        self.progress_bar.place(x=54, y=pb)
        # set bg color for individual widgets
        self.main_frame["bg"] = Player.BG
        self._repeat_btn["bg"], self._repeat_btn["fg"] = Player.BG, Player.FG
        self._play_btn["bg"], self._play_btn["fg"] = Player.BG, Player.FG
        self._next_btn["bg"], self._next_btn["fg"] = Player.BG, Player.FG
        self._shuffle["bg"], self._shuffle["fg"] = Player.BG, Player.FG
        self._previous_btn["bg"], self._previous_btn["fg"] = Player.BG, Player.FG
        self.current_time_label["bg"], self.current_time_label["fg"] = Player.BG, Player.FG
        self._title["bg"], self._title["fg"] = Player.BG, Player.FG
        self.playlist_btn["bg"] = Player.BG
        self.file_menu["bg"], self.file_menu["fg"] = Player.BG, Player.FG
        self.theme_menu["bg"], self.theme_menu["fg"] = Player.BG, Player.FG
        self.about_menu["bg"], self.about_menu["fg"] = Player.BG, Player.FG
        self._root.update_idletasks()

# ------------------------------------------------------------------------------------------------------------------------------

    def _manual_add(self):
        """
            Calls refresher function with open folder set to true
        """

        self._open_folder = 1
        self._refresher()

# ------------------------------------------------------------------------------------------------------------------------------

    def _repeat_ended(self):
        """
            Repeats playing songs in the just ended folder
        """
        if self.done_frame is not None:
            self.done_frame.pack_forget()
            self.done_frame = None
            self._init()
            self.collection_index = -1
            self.index = -1
            self.on_eos()

# ------------------------------------------------------------------------------------------------------------------------------

    def _refresher(self):
        """
            Updates folder files where necessry, or those passed as CL arguments
            Updates the title of window
            Shuffles the playlist
        """

        self.collection_index = -1
        all_files = []
        if len(PASSED_FILES) > 0:
            # if debug: print(PASSED_FILES)
            self._all_files = [i for i in PASSED_FILES if i.endswith(self._supported_extensions)]
            self._songspath = dirname(self._all_files[0])
            PASSED_FILES.clear()
            t = basename(self._songspath) if len(basename(self._songspath)) != 0 else "Disk"
            self._root.title(f"{t} - Lazy Selector")
            # change this implementation
            self.counta = Counta(self._songspath, dst=DATA_DIR, clean=all_files)
            self.on_eos()
        else:
            try:
                # try getting the current open folder
                file = Player._CONFIG["files"]["folder"]
                self._songspath = file
            except KeyError:
                # avoid 'name `file` is not defined' error
                file = ""
            if (self._open_folder) or (not exists(file)):
                # normalize path
                self._songspath = normpath(askdirectory(title="Choose a folder with audio/video files",
                                                        initialdir=expanduser("~\\"))
                                           )
            # when a user selects the same folder playing again
            if (file == self._songspath) and (self.index < len(self._all_files) - 1):
                # don't update the songs list
                pass
            else:
                # update
                try:
                    all_files = listdir(self._songspath)

                except FileNotFoundError:  # if Cancel clicked in the dialog _songspath == ''
                    # if log file isn't empty and the last song had played, update playlist
                    # executes when on clicks cancel on_eop
                    if (file != "") and (self.index >= len(self._all_files) - 1):
                        self._songspath = file
                        all_files = listdir(self._songspath)
                    # if no directory was chosen and the last song had not played, no updating playlist
                    elif (self._songspath == "") and (self.index <= len(self._all_files) - 1):
                        # avoid 'FileNotFound' error if _songspath remains an empty string
                        self._songspath = file

                    else:
                        if askokcancel("Lazy Selector",
                                       "\tA folder is required!\n    Do you want to select a folder again?"):
                            self._open_folder = 1
                            self._refresher()
                        else:
                            self._root.destroy()
                            sys.exit()
        if len(all_files) > 0:
            self.index = -1
            # change this implementation
            self.counta = Counta(self._songspath, dst=DATA_DIR, clean=all_files)
            try:
                Player._CONFIG.add_section("files")
            except Exception:
                pass
            Player._CONFIG.set("files", "folder", self._songspath)  # save to config file
            self._root.title("LOADING...")
            self._all_files = [i for i in all_files if i.endswith(self._supported_extensions)]

            shuffle(self._all_files)
            self._all_files.sort(key=self.counta.get_freq)

            t = basename(self._songspath) if len(basename(self._songspath)) != 0 else "Disk"
            self._root.title(f"{t} - Lazy Selector")
            if self.FORGET.get():
                if self.controls_frame is not None:
                    self._update_listbox()
                else:
                    if self.done_frame is not None:
                        self.done_frame.pack_forget()
                        self.done_frame = None
                        self._init()
            else:
                self._on_sort()
        # check if mixer state is just initialized or ended
        # set player to unloaded, not playing
        if not self._playing and (self.shuffle_mixer.state.value == 6 or self.shuffle_mixer.state.value == 0):
            self.collection_index = -1
            self._start = 0
            self._progress_variable.set(self._start)
            self.ftime = "00:00"
            self.current_time_label.configure(text=self.ftime)
            self._title_txt = ""
            self._title.configure(text=self._title_txt)
            self.play_btn_img = self.play_img
            self._play_btn.configure(image=self.play_btn_img)
            self._play_btn_command = self._unpause
            self._play_next_command = None
            self._play_prev_command = None
            self._play_btn["command"] = self._play_btn_command
            self._previous_btn["command"] = self._play_prev_command
            self._next_btn["command"] = self._play_next_command
        self._open_folder = 0

# ------------------------------------------------------------------------------------------------------------------------------

    def _loader(self):
        """
            returns the path to song at index
        """

        self.index += 1
        try:
            i = self._all_files[self.index]
        except IndexError:
            return 0
        filepath = join(self._songspath, i)
        if self.controls_frame is not None and not len(self.collected):
            self.listbox.selection_clear("end", 0)
            self.listbox.selection_set(self.index)
            self.listbox.see(self.index)
            self.listbox.activate(self.index)
        else:
            pass

        try:
            return filepath
        except Exception:
            pass

# ------------------------------------------------------------------------------------------------------------------------------

    def _select_fav(self):
        """
            Asks the user for filenames input
        """

        files_ = askopenfilenames(title="Choose audio/video files",
                                        filetypes=[("All files", "*")],
                                        initialdir=self.FILENAMES_INITIALDIR)
        loaded_files = [i for i in files_ if i.endswith(self._supported_extensions)]
        if len(loaded_files) >= 1 and len(self._loaded_files) == 0:
            self._loaded_files = [i for i in loaded_files]

        elif len(loaded_files) >= 1 and len(self._loaded_files) >= 1:
            for a in loaded_files:
                self._loaded_files.append(a)
        if len(loaded_files) >= 1:
            self._files_selected = 1
            self.FILENAMES_INITIALDIR = dirname(loaded_files[0])
            # remove song to avoid playing twice
            for audio in self._loaded_files:
                song = basename(audio)
                if song in self._all_files:
                    index = self._all_files.index(song)
                    self._all_files.remove(song)
                    if self.listbox is not None:
                        self.listbox.delete(index)
        else:
            self._files_selected = 0

# ------------------------------------------------------------------------------------------------------------------------------

    def _load_files(self):
        """
            Yields a path of songs added to queue by Add to Queue function
            Removes the song from list
        """

        for i in self._loaded_files:
            yield self._loaded_files.pop(0)  # get the first item in list

# ------------------------------------------------------------------------------------------------------------------------------

    def _mixer(self, load):
        """
            load media for playback
        """

        # for online streams, set playing to 0 here
        # since the program will take time to fetch stream for slow internet
        self._playing = 0
        try:
            # sometimes the online tab song title will display while playing local file
            # this happens on loading timeout and the play button is clicked for the first time
            if "googlevideo.com/videoplayback?" not in load:
                # assume it's a file
                self._title_txt = self._convert(splitext(basename(load))[0])
            self.shuffle_mixer.load(load)
            return self.shuffle_mixer
        except Exception:
            return self.shuffle_mixer

# ------------------------------------------------------------------------------------------------------------------------------

    def on_eos(self):
        """
            Play on shuffle
        """

        self._playing = 0
        self.isStreaming = 0
        self._start = 0
        self._progress_variable.set(self._start)
        self.play_btn_img = self.pause_img
        self._play_btn.configure(image=self.play_btn_img)

        if not self._files_selected:
            self._song = self._loader()
            if self._song:
                self._mixer(self._song).play()

        elif self._files_selected:
            try:
                self._song = next(self._load_files())
                self._mixer(self._song).play()
            except StopIteration:  # if it ever catches the error
                pass
            if len(self._loaded_files) == 0:  # avoid catching the StopIteration error above
                self._files_selected = 0

        if self._song:
            # wait for media meta to be parsed
            self._set_thread(self._updating, "Helper").start()

        if not self._song and not self.index:  # if self.index is 0; play or shuffle btn clicked once
            if self.shuffle_mixer.state.value == 0:
                self._playing = 0

            try:
                # showinfo is blocking
                showinfo(
                    "Lazy Selector",
                    f"{basename(self._songspath) if len(basename(self._songspath)) != 0 else 'Disk'} "
                    "folder has no audio/video files.\n\n   Choose a different folder.")
            except AttributeError:  # if self._songspath never initialized
                showinfo("Lazy Selector", "No folder initialized!")
            # open dir chooser after blocking
            self._manual_add()

        elif not self._song and self.index > len(self._all_files) - 1:
            # _stop_play has no effect if media has finished
            self._stop_play()
            self._on_eop()

# ------------------------------------------------------------------------------------------------------------------------------

    def _updating(self):
        """
            Helper function; set title; wait for metadata
        """
        self._update_labels("Loading...")
        self._playing = 0
        self._start = 0
        self._progress_variable.set(self._start)
        t = time()
        while 1:
            try:
                # if data_ready fails try using state
                if self.shuffle_mixer.data_ready or self.shuffle_mixer.state.value == 3:
                    try:  # If it's not first time of calling this function
                        self.duration_tip.unschedule()
                        self.duration_tip.hidetip()
                    except AttributeError:
                        pass
                    # if tab is local files or nothing was fetched from the internet; probably one's offline
                    # let's be able to select next in local files
                    # else let the online tab disable these commands
                    if not self.tab_num or self._title_link is None:
                        self.duration = round(self.shuffle_mixer.duration)
                        self.progress_bar["to"] = int(self.duration)

                    self._play_prev_command = lambda: self._play_prev()
                    self._play_next_command = lambda: self._play_prev(prev=0)
                    self._play_btn_command = self._stop_play
                    self._previous_btn["command"] = self._play_prev_command
                    self._play_btn["command"] = self._play_btn_command
                    self._next_btn["command"] = self._play_next_command
                    # _title_txt is defined in _on_click for online streaming; in the mixer func for local files
                    self._update_labels(self._title_txt)
                    self.duration_tip = ToolTip(self.progress_bar, f"Duration: {timedelta(seconds=self.duration)}")
                    self._playing = 1
                    self.change_stream = 1
                    break
                elif (time() - t) > self.TIMEOUT:
                    self.play_btn_img = self.play_img
                    self._play_btn.configure(image=self.play_btn_img)
                    self._update_labels("Timeout: Couldn't load media")
                    break
            except AttributeError:
                break

# ------------------------------------------------------------------------------------------------------------------------------

    def _play_prev(self, prev=1):
        """
            Play previous or next for local files
        """
        if not self.tab_num or self._title_link is None:
            self.play_btn_img = self.pause_img
            self._play_btn.configure(image=self.play_btn_img)
            self._playing = 0
            self._start = 0
            self._progress_variable.set(self._start)
            if prev:
                if len(self.collected) and self.collection_index > -1:
                    self.collection_index -= 1
                    if self.collection_index < 0:
                        self.collection_index = 0
                    i = self.collected[self.collection_index]
                else:
                    self.index -= 1
                    if self.index < 0:
                        self.index = 0
                    i = self._all_files[self.index]
                self._song = join(self._songspath, i)
            else:
                if len(self.collected) and self.collection_index > -1:
                    self.collection_index += 1
                    if self.collection_index > len(self.collected) - 1:
                        self.collection_index = len(self.collected) - 1
                    i = self.collected[self.collection_index]
                else:
                    self.index += 1
                    if self.index > len(self._all_files) - 1:
                        self.index = len(self._all_files) - 1
                    i = self._all_files[self.index]
                self._song = join(self._songspath, i)

            if self.controls_frame is not None:
                if self.collection_index > -1:
                    prev_index = self.collection_index
                    self.listbox.selection_clear("end", 0)
                    self.listbox.selection_set(prev_index)
                    self.listbox.see(prev_index)
                    self.listbox.activate(prev_index)
                elif self.collection_index == -1 and not len(self.collected):
                    prev_index = self.index
                    self.listbox.selection_clear("end", 0)
                    self.listbox.selection_set(prev_index)
                    self.listbox.see(prev_index)
                    self.listbox.activate(prev_index)
            self._mixer(self._song).play()
            # wait for media meta to be parsed
            self._set_thread(self._updating, "Helper").start()
        else:
            if self.change_stream and prev:
                self.stream_index -= 1
                self.stream_manager()
            if self.change_stream and not prev:
                self.stream_index += 1
                self.stream_manager()

# ------------------------------------------------------------------------------------------------------------------------------

    def _onoff_repeat(self):
        """
            Toggle player loop
        """

        self._active_repeat = not self._active_repeat
        self.shuffle_mixer.loop = self._active_repeat
        # update tooltip and image according to theme and playback mode
        self.check_theme_mode()

# ------------------------------------------------------------------------------------------------------------------------------

    def check_theme_mode(self):
        """
            Change playback mode img according to theme set
            Update tooltips
        """
        if self._playing:
            self.duration_tip = ToolTip(self.progress_bar, f"Duration: {timedelta(seconds=self.duration)}")
        if Player.BG == "gray97" and self.main_frame is not None:
            self.rpo_image = PhotoImage(data=POINTER_IMG)
            if self._active_repeat:
                im = REPEAT_IMG
                ToolTip(self._repeat_btn, "Repeat")
            else:
                ToolTip(self._repeat_btn, "Shuffle")
                im = SHUFFLE_IMG
        else:
            self.rpo_image = PhotoImage(data=DARKPOINTER_IMG)
            if self._active_repeat:
                im = DARKREPEAT_IMG
                ToolTip(self._repeat_btn, "Repeat")
            else:
                ToolTip(self._repeat_btn, "Shuffle")
                im = DARKSHUFFLE_IMG
        self._repeat_image = PhotoImage(data=im)
        self._repeat_btn.configure(image=self._repeat_image)
        if self.main_frame is not None:
            self.playlist_btn.configure(image=self.rpo_image)

# ------------------------------------------------------------------------------------------------------------------------------

    def _kill(self):
        """
            Confirm exit if playing, save modifications
        """
        try:
            try:
                # remove read-only
                chmod(DATA_DIR + "\\lazylog.cfg", S_IWUSR | S_IREAD)
            except Exception:
                pass
            Player._CONFIG.set("theme", "forget", str(self.FORGET.get()))
            Player._CONFIG.set("files", "search", self.search_str)
            # if mixer paused
            if self.shuffle_mixer.state.value == 4:
                if askokcancel("Lazy Selector", "Lazy Selector Music is still playing.\n      Quit Anyway?"):

                    try:
                        Player._CONFIG.add_section("window")
                    except Exception:
                        pass
                    Player._CONFIG.set("window", "position", f"{self._root.winfo_x()}+{self._root.winfo_y()}")
                    try:
                        with open(DATA_DIR + "\\lazylog.cfg", "w") as f:
                            Player._CONFIG.write(f)
                    except Exception:
                        pass
                    # set read-only attr; unsupported from this version onwards
                    # chmod(DATA_DIR + "\\lazylog.cfg", S_IREAD | S_IRGRP | S_IROTH)
                    self.shuffle_mixer.delete()
                    self._root.destroy()
                    sys.exit(0)
            else:
                # pause first
                self._stop_play()
                try:
                    Player._CONFIG.add_section("window")
                except Exception:
                    pass
                Player._CONFIG.set("window", "position", f"{self._root.winfo_x()}+{self._root.winfo_y()}")
                try:
                    with open(DATA_DIR + "\\lazylog.cfg", "w") as f:
                        Player._CONFIG.write(f)
                except Exception:
                    pass
                # set read-only attr; unsupported from this version onwards
                # chmod(DATA_DIR + "\\lazylog.cfg", S_IREAD | S_IRGRP | S_IROTH)
                self.shuffle_mixer.delete()
                self._root.destroy()
                sys.exit(0)
        except Exception:
            self.shuffle_mixer.delete()
            self._root.destroy()
            sys.exit(1)

# ------------------------------------------------------------------------------------------------------------------------------

    def _update_labels(self, song):
        """
            Updates all labels that need update on change of song
            Aligns the title text
        """

        self._title.configure(text=song.encode("utf-8"))

# ------------------------------------------------------------------------------------------------------------------------------

    def _remove_pref(self):
        """delete prefs"""
        try:
            if self.reset_preferences:
                Player._CONFIG.set("theme", "bg", Player.BG)
                Player._CONFIG.set("theme", "fg", Player.FG)
                self.FORGET.set(1)
                self.reset_preferences = 0
            else:
                Player._CONFIG.set("theme", "bg", "gray28")
                Player._CONFIG.set("theme", "fg", "gray97")
                self.FORGET.set(0)
                self.reset_preferences = 1
        except Exception:
            pass

# ------------------------------------------------------------------------------------------------------------------------------
    def _about(self):
        """
            Shows information about the player
        """

        if self.top is None:
            self.top = Toplevel()
            self.top.wm_protocol("WM_DELETE_WINDOW", self._kill_top)
            self.top.wm_title("About - Lazy Selector")
            position = f"{self._root.winfo_x() - 10}+{self._root.winfo_y()}"
            self.top.geometry("355x630+" + position)
            self.top.resizable(0, 0)
            side = "nw"

            def mailto(event):
                subject = "Lazy Selector Version 4.2"
                body = "Hello, Ernesto!".replace(" ", "%20")
                webbrowser.open(f"mailto:?to=ernestondieki12@gmail.com&subject={subject}&body={body}", new=1)

            display_text = Label(self.top, pady=10, padx=50, fg="DeepSkyBlue4",
                                 text="Lazy Selector\nVersion: 4.2\nDeveloped by: Ernesto\nernestondieki12@gmail.com",
                                 font=("arial", 12, "bold"), relief="groove")
            display_text.pack(pady=10)
            ToolTip(display_text, "Contact the Developer")
            display_text.bind("<ButtonRelease-1>", mailto)
            display_text.bind("<Return>", mailto)
            self.display_canvas = Canvas(self.top, height=4000)
            self.top_scrollbar = Scrollbar(self.top, command=self.display_canvas.yview)
            self.display_canvas.config(yscrollcommand=self.top_scrollbar.set)
            self.top_scrollbar.pack(side="right", fill="y")
            self.display_canvas.pack(expand=1)

            def canvas_xy():
                # (39, 3, 373, 195) -> (x1 left, x2 right, y1 top, y2 bottom)
                area = self.display_canvas.bbox("all")
                try:
                    # x1 left, y2 bottom
                    return area[0] + 1, area[3] + 20
                # for the first item, use 40, 10
                except TypeError:
                    return 40, 10
            text_font = ("New Times Roman", 8, "bold")
            self.image1 = PhotoImage(data=FIRST_IMG)
            self.display_canvas.create_text(canvas_xy(), text=" Dark themed window.", anchor="w", font=text_font)
            self.display_canvas.create_image(canvas_xy(), image=self.image1, anchor=side)

            self.image2 = PhotoImage(data=SECOND_IMG)
            self.display_canvas.create_text(canvas_xy(), text=" (Click the arrow to navigate to the playlist and back.)\n Light themed window.", anchor="w", font=text_font)
            self.display_canvas.create_image(canvas_xy(), image=self.image2, anchor=side)

            self.image3 = PhotoImage(data=THIRD_IMG)
            self.display_canvas.create_text(canvas_xy(), text=" Easy switching between local and online streams tabs.",
                                            anchor="nw", font=text_font)
            self.display_canvas.create_image(canvas_xy(), image=self.image3, anchor=side)

            self.image4 = PhotoImage(data=FOURTH_IMG)
            self.display_canvas.create_text(canvas_xy(), text=" Right-click on a track for more options.",
                                            anchor="w", font=text_font)
            self.display_canvas.create_image(canvas_xy(), image=self.image4, anchor=side)

            self.image5 = PhotoImage(data=FIFTH_IMG)
            self.display_canvas.create_text(canvas_xy(),
                                            text=" Searched tracks gives more options than the playlist.\n  'Play Next in Playlist' plays next in the main playlist.",
                                            anchor="w", font=text_font)
            self.display_canvas.create_image(canvas_xy(), image=self.image5, anchor=side)

            # self.image6 = PhotoImage(data=SIXTH_IMG)
            self.display_canvas.create_text(canvas_xy(),
                                            text="  Streaming capabalities in 'Online streams' tab.\n  This online playlist plays in loop mode.\n  Get a fast Wi-Fi for a faster streaming experience. Enjoy!",
                                            anchor="nw", font=text_font)
            # self.display_canvas.create_image(canvas_xy(), image=self.image6, anchor=side)

            self.image7 = PhotoImage(data=SEVENTH_IMG)
            self.display_canvas.create_text(canvas_xy(), text="  Displays connection errors.", anchor="w", font=text_font)
            self.display_canvas.create_image(canvas_xy(), image=self.image7, anchor=side)

            self.image11 = PhotoImage(data=SOKORO_IMG)
            self.display_canvas.create_text(95, canvas_xy()[1] + 20, text="In loving memory of grandpa, Joseph", anchor="w", font=("New Times Roman", 10, "italic bold"))
            self.display_canvas.create_image(180, canvas_xy()[1], image=self.image11, anchor=side)
            self.display_canvas.config(scrollregion=self.display_canvas.bbox("all"))
            self.display_canvas.bind("<MouseWheel>", self.scroll_widget)
            self._root.withdraw()
        # get focus, normal focus_set not working
        self.top.focus_force()

# ------------------------------------------------------------------------------------------------------------------------------

    def _kill_top(self):
        self._root.deiconify()
        self.top.destroy()
        self.top = None

# ------------------------------------------------------------------------------------------------------------------------------

    def _update_color(self, bg, fg):
        """
            Switches between themes
            Usage: self._update_color(background:str, foreground:str)
        """

        if self.main_frame is not None:
            Player.BG = bg
            Player.FG = fg
            Player.MN = bg
            try:
                Player._CONFIG.add_section("theme")
            except Exception:
                pass
            if not self.reset_preferences:
                Player._CONFIG.set("theme", "bg", Player.BG)
                Player._CONFIG.set("theme", "fg", Player.FG)
            self.check_theme_mode()
            self._update_theme()

# ------------------------------------------------------------------------------------------------------------------------------

    def _stop_play(self):
        """
            Pauses playback
        """
        if self._play_btn_command is not None:
            self._playing = 0
            self._play_btn["state"] = "disabled"
            self.play_btn_img = self.play_img
            self._play_btn_command = self._unpause
            self._play_btn.configure(image=self.play_btn_img)
            self._play_btn["command"] = self._play_btn_command
            self.shuffle_mixer.pause()
            self._play_btn["state"] = "normal"

    def _unpause(self):
        """
            Starts/Resumes playback
        """

        if self._play_btn_command is not None and self.shuffle_mixer.state.value == 4:
            self._play_btn_command = self._stop_play
            self.play_btn_img = self.pause_img
            self._play_btn.configure(image=self.play_btn_img)
            self._play_btn["command"] = self._play_btn_command
            self.shuffle_mixer.play()
            self._playing = 1
        elif self.shuffle_mixer.state.value == 0 or self.shuffle_mixer.state.value == 6:
            self.on_eos()
            self._root.focus_set()

# ------------------------------------------------------------------------------------------------------------------------------

    def _set_thread(self, func, nm, c=()):
        """
            setup a daemon thread
        """

        return Thread(target=func, args=c, daemon=1, name=nm)

# ------------------------------------------------------------------------------------------------------------------------------

    def format_time(self):
        """ format elapsed time for display """
        if self._start >= 3600:
            self._root.update_idletasks()
            self.ftime = timedelta(seconds=self._start)
        else:
            mins, secs = divmod(self._start, 60)
            self.ftime = f"{round(mins):02}:{round(secs):02}"

# ------------------------------------------------------------------------------------------------------------------------------

    def _slide(self, value):
        """
            Seeks and updates value of slider
        """
        # not really DRY, thought of nesting a function but overheads!
        # if playing
        if self._playing:
            self._playing = 0
            value = round(float(value))
            self._progress_variable.set(value)
            self._start = self._progress_variable.get()
            # convert to ms
            self.shuffle_mixer.seek(value * 1000)
            self._playing = 1
        # else if paused
        elif self.shuffle_mixer.state.value == 4:
            self._unpause()
            # value = round(float(value))
            # self._progress_variable.set(value)
            # self._start = self._progress_variable.get()
            # # convert to ms
            # self.shuffle_mixer.seek(value * 1000)
            # self.format_time()
            # self.current_time_label.configure(text=self.ftime)

# ------------------------------------------------------------------------------------------------------------------------------

    def _set_uptime(self):
        """
            Updates current time, updates idletasks and checks for eos and battery
        """

        said = 0
        while 1:
            try:
                if self._playing:
                    # player ended status
                    if (self.shuffle_mixer.state.value == 6 and not self._active_repeat):

                        if len(self.collected) > 0 and self.controls_frame is not None and self.collection_index > -1:
                            self.collection_index += 1
                            self.listbox.selection_clear(0, "end")
                            self._collection_manager()

                        elif self.isStreaming and self._title_link is not None and self.tab_num:
                            if self.change_stream:
                                self.stream_index += 1
                                self.stream_manager()
                        else:
                            try:
                                if exists(self._song):
                                    # add 1 to play frequency
                                    self.counta.log_item(basename(self._song), self.counta.get_freq(basename(self._song)) + 1)
                            except AttributeError:
                                pass
                            self.on_eos()
                        self._root.update_idletasks()
                    # playing status
                    elif self.shuffle_mixer.state.value == 3:
                        self._start = round(self.shuffle_mixer.time)
                        # format time for display
                        self.format_time()

                        self.current_time_label.configure(text=self.ftime)
                        # duration can change for online streams
                        self.duration = round(self.shuffle_mixer.duration)
                        self.progress_bar.configure(to=int(self.duration))
                        self._progress_variable.set(self._start)
                        self._update_labels(self._title_txt)
                        self.progress_bar.update_idletasks()
                        sleep(1)
                        if battery.get_state()["percentage"] < 41 and not said:
                            # a reminder
                            notification.notify(title="Lazy Selector",
                                                message=f'{battery.get_state()["percentage"]}% Charge Available',
                                                app_name="Lazy Selector",
                                                timeout=180,
                                                app_icon=DATA_DIR + "\\app.ico" if exists(DATA_DIR + "\\app.ico") else None)
                            said = 1
                    # player ended
                    elif self.shuffle_mixer.state.value == 6:
                        sleep(1)

                else:
                    if battery.get_state()["percentage"] < 41 and not said:
                        # a reminder
                        notification.notify(title="Lazy Selector",
                                            message=f'{battery.get_state()["percentage"]}% Charge Available',
                                            app_name="Lazy Selector",
                                            timeout=180,
                                            app_icon=DATA_DIR + "\\app.ico" if exists(DATA_DIR + "\\app.ico") else None)
                        said = 1
                    sleep(1)
            except AttributeError:
                self._set_thread(self._set_uptime, "Timer").start()

# ------------------------------------------------------------------------------------------------------------------------------

    def _collection_manager(self):
        """
            Plays, checks index and loops in searched songs
        """

        self._playing = 0
        if self.collection_index > len(self.collected) - 1:
            self.collection_index = 0
        # if debug: print("Collection Manager Index after:", self.collection_index)
        self.listbox.selection_set(self.collection_index)
        self.listbox.see(self.collection_index)
        self.listbox.activate(self.collection_index)
        self._on_click()

    def stream_manager(self):
        """
            Plays, checks index and loops in online streams
        """

        self._playing = 0
        self.listview.selection_clear(0, "end")
        if (self.stream_index > len(self._title_link) - 1) or (self.stream_index < 0):
            self.stream_index = 0
        self.listview.selection_set(self.stream_index)
        self.listview.see(self.stream_index)
        self.listview.activate(self.stream_index)
        self._on_click()
        self.isStreaming = 1

# ------------------------------------------------------------------------------------------------------------------------------

    def _prioritize(self, sequence=None, keywords=None):
        """
            Insert match of sequence at index 0
        """
        # if debug: print(keywords)
        if keywords is None or len(keywords) < 3 or keywords == "":
            pass
        else:
            keys = keywords.strip().lower().split(" ")
            for item in sequence:
                i = SPLIT("[- _.,;]", item.lower())
                for keyword in keys:
                    if keyword in i:
                        sequence.remove(item)
                        sequence.insert(0, item)

# --------------------------------------------------------------------------------------------------------------------------------

    def _sort_by_keys(self, event=None):

        keys = self.keywords_shelf.get()
        self._prioritize(self._all_files, keywords=keys)
        self._init()


PASSED_FILES = sys.argv[1:]


current_pid = getpid()


def close_prev():
    for line in popen("tasklist").readlines():
        if line.startswith("Lazy_Selector.exe"):
            if line.split()[1] != str(current_pid):
                s = STARTUPINFO()
                s.dwFlags |= STARTF_USESHOWWINDOW
                call(f"taskkill /F /PID {line.split()[1]}", startupinfo=s)
                break


Thread(target=close_prev, daemon=1).start()

# tk = Tk()
# p = Player(tk)
# tk.mainloop()
try:
    tk = Tk()
    p = Player(tk)
    tk.mainloop()
except Exception:
    tk.destroy()

p.shuffle_mixer.release_sleep()
print("LEAVING...")
sys.exit(1)
# TODO
# pass song to queue of already playing player
