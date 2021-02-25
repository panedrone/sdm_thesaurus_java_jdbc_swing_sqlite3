import datetime

import os
import sys
from copy import deepcopy

import requests
import tkinter as tk

from tkinter import messagebox
from dotenv import dotenv_values

from dal.DataStore import DataStore
from dal.DownloadsInfo import DownloadsInfo
from dal.DownloadsDao import DownloadsDao
from dal.Release import Release
from dal.ReleasesDao import ReleasesDao

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# https://docs.github.com/en/rest/reference/repos#releases

# Is there possibility to get releases with pyGithub
# https://stackoverflow.com/questions/40462632/is-there-possibility-to-get-releases-with-pygithub


class MyApp:
    CHART_WIDTH = 480
    CHART_HEIGHT = 320

    def __init__(self):
        # === panedrone: not needed:
        # root.geometry("600x300")
        self.ds = DataStore()
        self.ds.open()
        self.d_dao = DownloadsDao(self.ds)
        self.p_dao = ReleasesDao(self.ds)
        self.root = tk.Tk()
        self.root.resizable(width=False, height=False)
        frame = tk.Frame(self.root)
        pad = 8
        frame.pack(padx=pad, pady=pad)
        self.label_release_info = tk.Label(frame, bd=1, padx=pad)
        self.label_release_info.grid(column=0, row=0)
        canvas_panel = tk.PanedWindow(frame, relief='sunken', bd=1)
        canvas_panel.grid(column=1, row=0, padx=(pad, 0))
        # === panedrone: don't use tk.Label as Canvas container because of buggy repaint behavior
        self.canvas = tk.Canvas(canvas_panel, relief='sunken', width=self.CHART_WIDTH, height=self.CHART_HEIGHT)
        self.canvas.pack()  # the same as fill=tk.BOTH
        b = tk.Button(frame, text="Update", command=self._show_stat, bd=1)
        b.grid(column=1, row=1, pady=(pad, 0), sticky="E")
        self.release_path = Release()
        self._show_stat()
        # center it last:
        self.root.eval('tk::PlaceWindow . center')

    def run(self):
        self.root.mainloop()

    def _load_settings(self):
        if len(sys.argv) > 1:
            env = sys.argv[1]
        else:
            env = '.env'
        dotenv_path = os.path.join(os.path.dirname(__file__), env)
        values = dotenv_values(dotenv_path)
        user = values.get("USER")
        repo = values.get("PERO")
        tag_name = values.get("TAG")
        r_name = f"{user}/{repo}/{tag_name}"
        found = self.p_dao.find_by_name(r_name)
        if len(found) == 0:
            self.release_path = Release()
            self.release_path.r_name = r_name
            self.p_dao.create_release(self.release_path)
            self.ds.commit()
        else:
            self.release_path = found[0]
        return user, repo, tag_name

    REPORT_RANGE_IN_DAYS = 14

    def _prepare_chart_data(self):
        # read an extra one
        res = self.d_dao.get_latest_ordered_by_date_desc(self.release_path.r_id, 0, self.REPORT_RANGE_IN_DAYS + 1)
        if len(res) == 0:
            return res, 0
        if len(res) == 1:
            return res, res[0].d_downloads
        res = sorted(res, key=lambda d: d.d_downloads)
        tmp = deepcopy(res)
        downloads_max = -1
        for i in range(1, len(res)):
            curr = res[i]
            prev = tmp[i - 1]
            diff = curr.d_downloads - prev.d_downloads
            curr.d_downloads = diff
            if diff > downloads_max:
                downloads_max = diff
        return res, downloads_max

    def _get_chart_data(self):
        prepared, downloads_max = self._prepare_chart_data()
        prepared_dict = {}
        for di in prepared:
            prepared_dict[di.d_date] = di
        today = datetime.date.today()
        downloads_by_dates = []
        for days_to_add in range(self.REPORT_RANGE_IN_DAYS):
            dt = today - datetime.timedelta(days=days_to_add)
            dt = str(dt)
            if dt in prepared_dict:
                downloads_by_date = prepared_dict[dt].d_downloads
            else:
                downloads_by_date = 0
            dt = dt.split("-")[2]
            downloads_by_dates.append((dt, downloads_by_date))
        downloads_by_dates = sorted(downloads_by_dates, reverse=False)
        return downloads_by_dates, downloads_max

    def _build_chart(self):
        data, max_data_value = self._get_chart_data()
        if max_data_value == 0:
            max_data_value = 1
        # https://stackoverflow.com/questions/35666573/use-tkinter-to-draw-a-specific-bar-chart
        y_stretch = (self.CHART_HEIGHT - 60) / max_data_value
        y_gap = 24
        x_stretch = 14
        x_width = 20
        x_gap = 12
        self.canvas.delete("all")
        for x, y_tuple in enumerate(data):
            day, y = y_tuple
            x0 = x * x_stretch + x * x_width + x_gap
            y0 = self.CHART_HEIGHT - (y * y_stretch + y_gap)
            x1 = x * x_stretch + x * x_width + x_width + x_gap
            y1 = self.CHART_HEIGHT - y_gap
            hex_color = "#%02x%02x%02x" % (109, 170, 44)
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=hex_color)
            text_1 = self.canvas.create_text(x0, y0, anchor="nw", text=str(y))
            x_rect_offset = ((x1 - x0) / 2)
            self._center_align(text_1, x_rect_offset)
            text_2 = self.canvas.create_text(x0, y1 + 20, anchor="nw", text=str(day))
            self._center_align(text_2, x_rect_offset)

    def _center_align(self, text_id, x_rect_offset):
        text_box = self.canvas.bbox(text_id)
        text_box_x0 = text_box[0]
        text_box_x1 = text_box[2]
        x_text_offset = ((text_box_x1 - text_box_x0) / 2)
        # https://stackoverflow.com/questions/28754224/tkinter-how-to-horizontally-center-canvas-text
        self.canvas.move(text_id, x_rect_offset - x_text_offset, -16)

    def _update_ui(self, text):
        self.label_release_info.config(text=text)
        self._build_chart()

    def _update_db(self, release_downloads_count):
        today = datetime.date.today()
        today = str(today)
        downloads_arr = self.d_dao.find(str(self.release_path.r_id), today)
        if len(downloads_arr) == 0:
            di = DownloadsInfo()
            di.r_id = self.release_path.r_id
            di.d_date = today
            di.d_downloads = release_downloads_count
            self.d_dao.create_download(di)
            self.ds.commit()
        else:
            if downloads_arr[0].d_downloads != release_downloads_count:
                downloads_arr[0].d_downloads = release_downloads_count
                self.d_dao.update_download(downloads_arr[0])
                self.ds.commit()

    @staticmethod
    def _get_release_header(release):
        tag = release.get('tag_name')
        if not tag:
            tag_url = release['html_url']
            _, tag = os.path.split(tag_url)
        published_at = release.get('published_at')
        if published_at:
            published_at = published_at.split("T")[0]
        release_name = release.get('name')
        if not release_name:
            release_name = f"'{tag}'"
        return tag, release_name, published_at

    def _process_releases(self, releases, tag_name) -> str:
        release_files_info = ''
        total_downloads = 0
        release_info = None
        for release in releases:
            tag, release_name, published_at = self._get_release_header(release)
            release_downloads_count = 0
            for file in release['assets']:
                dc = file.get('download_count')
                if isinstance(dc, int):
                    file_download_count = dc
                else:
                    file_download_count = int(dc)
                release_downloads_count += file_download_count
                if tag_name == tag:
                    file_name = file['name']
                    release_files_info += f'\n{file_name}: {file_download_count}'
            if tag_name == tag:
                self._update_db(release_downloads_count)
                release_info = f"Release {release_name}\n\n" \
                               f"Published at {published_at}\n" \
                               f"{release_files_info}\n\n" \
                               f"Downloads: {release_downloads_count}"
            total_downloads += release_downloads_count
        return f'{release_info}\n\nTotal Downloads: {total_downloads}'

    def _show_stat(self):
        try:
            user, repo, tag_name = self._load_settings()
            self.root.title(f'{user}/{repo}/{tag_name}')
            url = f'https://api.github.com/repos/{user}/{repo}/releases'
            response = requests.get(url)
            response.raise_for_status()
            releases = response.json()
            # with open("release.json", 'w+') as fileToSave:
            #     json.dump(releases, fileToSave, ensure_ascii=True, indent=4, sort_keys=True)
            release_info = self._process_releases(releases, tag_name)
            self._update_ui(release_info)
        except Exception as e:
            logger.exception(e)
            messagebox.showerror(title='Error', message=e)


if __name__ == '__main__':
    app = MyApp()
    app.run()
