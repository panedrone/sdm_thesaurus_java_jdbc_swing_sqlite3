#! /usr/bin/python3
import datetime

import os
import sys
from copy import deepcopy

import requests
import tkinter as tk

from tkinter import messagebox

from dateutil import parser
from dotenv import dotenv_values

from dal.data_store import DataStore
from dal.downloads import Downloads
from dal.downloads_dao import DownloadsDao
from dal.release_data import ReleaseData
from dal.releases_dao import ReleasesDao

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# https://docs.github.com/en/rest/reference/repos#releases

# Is there possibility to get releases with pyGithub
# https://stackoverflow.com/questions/40462632/is-there-possibility-to-get-releases-with-pygithub


class MyApp:
    CHART_WIDTH = 480
    CHART_HEIGHT = 320

    REPORT_RANGE = 14

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
        buttons_panel = tk.PanedWindow(frame)
        buttons_panel.grid(column=1, row=1, pady=(pad, 0), sticky="E")
        tk.Button(buttons_panel, text="Update", command=self.show_stat2, bd=1).grid(column=0, row=0, padx=(pad, 0))
        tk.Button(buttons_panel, text="Raw", command=self.show_raw, bd=1).grid(column=1, row=0, padx=(pad, 0))
        tk.Button(buttons_panel, text="By Days", command=self.show_by_days, bd=1).grid(column=2, row=0, padx=(pad, 0))
        self.release_data = ReleaseData()
        self.raw_stat = False
        self.release_info_file_path = None
        self.show_stat(False)
        # center it last:
        self.root.eval('tk::PlaceWindow . center')

    def run(self):
        self.root.mainloop()

    def show_raw(self):
        self.raw_stat = True
        self.show_stat(False)

    def show_by_days(self):
        self.raw_stat = False
        self.show_stat(False)

    def show_stat2(self):
        self.show_stat(True)

    def load_settings_and_data(self):
        if len(sys.argv) > 1:
            env = sys.argv[1]
        else:
            env = '.env'
        dotenv_path = os.path.join(os.path.dirname(__file__), env)
        values = dotenv_values(dotenv_path)
        user = values.get("USER")
        repo = values.get("REPO")
        tag_name = values.get("TAG")
        r_name = f"{user}/{repo}/{tag_name}"
        found = self.p_dao.find_by_name(r_name)
        if len(found) == 0:
            self.release_data = ReleaseData()
            self.release_data.r_name = r_name
            self.p_dao.create_release(self.release_data)
            self.ds.commit()
        else:
            self.release_data = found[0]
        return user, repo, tag_name

    def prepare_chart_data(self):
        # read an extra one
        raw = self.d_dao.get_latest_ordered_by_date_desc(self.release_data.r_id, 0, self.REPORT_RANGE + 1)
        raw = sorted(raw, key=lambda d: d.d_date)
        tmp = deepcopy(raw)
        by_days = deepcopy(raw)
        for i in range(1, len(by_days)):
            curr = by_days[i]
            prev = tmp[i - 1]
            if prev.d_downloads > curr.d_downloads:
                diff = curr.d_downloads
            else:
                diff = curr.d_downloads - prev.d_downloads
            curr.d_downloads = diff
        return raw, by_days

    def get_chart_data(self):
        raw, by_days = self.prepare_chart_data()
        raw_dict = {}
        for di in raw:
            raw_dict[di.d_date] = di
        by_days_dict = {}
        for di in by_days:
            by_days_dict[di.d_date] = di
        today = datetime.date.today()
        downloads_max = -1
        downloads_data = []
        sum_for_period = 0
        for days_to_add in range(self.REPORT_RANGE):
            dt = today - datetime.timedelta(days=days_to_add)
            dt = str(dt)
            if dt in by_days_dict:
                dt_downloads = by_days_dict[dt].d_downloads
                sum_for_period += dt_downloads
                if self.raw_stat:
                    dt_downloads = raw_dict[dt].d_downloads
            else:
                dt_downloads = 0
            if dt_downloads > downloads_max:
                downloads_max = dt_downloads
            downloads_data.append((dt, dt_downloads))
        downloads_data = sorted(downloads_data, reverse=False)
        return downloads_data, downloads_max, sum_for_period

    def build_chart(self):
        data, max_data_value, sum_for_period = self.get_chart_data()
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
            day = day.split("-")[2]
            x0 = x * x_stretch + x * x_width + x_gap
            y0 = self.CHART_HEIGHT - (y * y_stretch + y_gap)
            x1 = x * x_stretch + x * x_width + x_width + x_gap
            y1 = self.CHART_HEIGHT - y_gap
            hex_color = "#%02x%02x%02x" % (109, 170, 44)
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=hex_color)
            text_1 = self.canvas.create_text(x0, y0, anchor="nw", text=str(y))
            x_rect_offset = ((x1 - x0) / 2)
            self.center_align(text_1, x_rect_offset)
            text_2 = self.canvas.create_text(x0, y1 + 20, anchor="nw", text=str(day))
            self.center_align(text_2, x_rect_offset)
        return sum_for_period

    def center_align(self, text_id, x_rect_offset):
        text_box = self.canvas.bbox(text_id)
        text_box_x0 = text_box[0]
        text_box_x1 = text_box[2]
        x_text_offset = ((text_box_x1 - text_box_x0) / 2)
        # https://stackoverflow.com/questions/28754224/tkinter-how-to-horizontally-center-canvas-text
        self.canvas.move(text_id, x_rect_offset - x_text_offset, -16)

    def update_ui(self, text):
        sum_for_period = self.build_chart()
        avg_for_period = round(sum_for_period / self.REPORT_RANGE, 1)
        if text:
            text += f"{avg_for_period} times a day in last {self.REPORT_RANGE}\n"
            self.label_release_info.config(text=text)

    def update_db(self, release_downloads_count):
        today = datetime.date.today()
        today = str(today)
        downloads_arr = self.d_dao.find(str(self.release_data.r_id), today)
        if len(downloads_arr) == 0:
            di = Downloads()
            di.r_id = self.release_data.r_id
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
    def get_release_header(release):
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

    def parse_github_response(self, releases_json, tag_name) -> str:
        release_files_info = ''
        total_downloads = 0
        release_info = None
        today = datetime.date.today()
        published_min = today
        for release in releases_json:
            tag, release_name, published_at = self.get_release_header(release)
            published_dt = parser.parse(published_at).date()
            if published_dt < published_min:
                published_min = published_dt
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
                self.update_db(release_downloads_count)
                release_info = self.get_release_info(release_name, published_at, release_downloads_count)
                release_info += f"{release_files_info}"
            total_downloads += release_downloads_count
        days_from_start_date, avg_downloads_a_day = self.get_period_info(published_min, total_downloads)
        return f'{release_info}\n\nStarted at {published_min}\n' \
               f'{days_from_start_date} days ago\n' \
               f'{total_downloads} downloads\n' \
               f'{avg_downloads_a_day} times a day\n'

    @staticmethod
    def get_period_info(dt_period_start, period_downloads_count):
        dt_today = datetime.date.today()
        days_from_start_date = (dt_today - dt_period_start).days - 1  # today's one is mainly incomplete
        if days_from_start_date > 0:
            avg_downloads_a_day = round(period_downloads_count / days_from_start_date, 1)
        else:
            days_from_start_date = 0
            avg_downloads_a_day = period_downloads_count
        return days_from_start_date, avg_downloads_a_day

    def get_release_info(self, release_name, published_at, release_downloads_count):
        published_dt = parser.parse(published_at).date()
        days_from_start_date, avg_downloads_a_day = self.get_period_info(published_dt, release_downloads_count)
        release_info = f"Release {release_name}\n" \
                       f"Published at {published_at}\n" \
                       f"{days_from_start_date} days ago\n" \
                       f"{release_downloads_count} downloads\n" \
                       f"{avg_downloads_a_day} times a day\n"
        return release_info

    def show_stat(self, query_github):
        try:
            user, repo, tag_name = self.load_settings_and_data()
            self.root.title(f'{user}/{repo}/{tag_name}')
            self.release_info_file_path = f"./{user}.{repo}.{tag_name}.txt"
            if not query_github:
                release_info = None
                if os.path.isfile(self.release_info_file_path):
                    with open(self.release_info_file_path, "r") as file:
                        release_info = file.read()
                if not release_info:
                    release_info = "Click 'Update'\nfor recent stat from GitHub\n"
                self.update_ui(release_info)
                return
            url = f'https://api.github.com/repos/{user}/{repo}/releases'
            response = requests.get(url)
            response.raise_for_status()
            releases_json = response.json()
            # with open("release.json", 'w+') as fileToSave:
            #     json.dump(releases, fileToSave, ensure_ascii=True, indent=4, sort_keys=True)
            release_info = self.parse_github_response(releases_json, tag_name)
            # release_info = "?\n"
            self.update_ui(release_info)
            with open(self.release_info_file_path, "w") as file:
                file.write(release_info)
        except Exception as e:
            logger.exception(e)
            messagebox.showerror(title='Error', message=e)


if __name__ == '__main__':
    app = MyApp()
    app.run()
