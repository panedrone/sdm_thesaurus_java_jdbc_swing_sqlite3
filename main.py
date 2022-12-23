#! /usr/bin/python3
import datetime

import os
import sys
# from threading import Thread
import time
from threading import Thread

import requests
import tkinter as tk

from tkinter import messagebox
from tkcalendar import DateEntry

from dateutil import parser, relativedelta
from dotenv import dotenv_values

from dal.data_store import create_ds
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
    CHART_WIDTH = 1024
    CHART_HEIGHT = 320

    REPORT_RANGE = 30

    def __init__(self):
        self.ds = create_ds()
        self.root = tk.Tk()
        self.root.resizable(width=False, height=False)

        self.root.withdraw()  # hide it before ANY changes of content

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
        self.count = tk.Label(buttons_panel, text="?")
        self.count.grid(column=0, row=0, padx=(pad, 0))
        tk.Button(buttons_panel, text="Update", command=self.update_and_show_stat, bd=1).grid(column=1, row=0,
                                                                                              padx=(pad, 0))
        tk.Button(buttons_panel, text="Raw", command=self.show_raw, bd=1).grid(column=2, row=0, padx=(pad, 0))
        tk.Button(buttons_panel, text="Past 30 days", command=self.show_by_days, bd=1).grid(column=3, row=0,
                                                                                            padx=(pad, 0))
        self.cal = DateEntry(buttons_panel, date_pattern='yyyy-mm-dd')
        self.cal.grid(column=4, row=0, padx=(pad, 0))
        tk.Button(buttons_panel, text="<", command=self.by_days_prev, bd=1).grid(column=5, row=0, padx=(pad, 0))
        tk.Button(buttons_panel, text=">", command=self.by_days_next, bd=1).grid(column=6, row=0, padx=(pad, 0))
        tk.Button(buttons_panel, text="t", command=self.by_days, bd=1).grid(column=7, row=0, padx=(pad, 0))
        tk.Button(buttons_panel, text="By month", command=self.show_by_month, bd=1).grid(column=8, row=0, padx=(pad, 0))
        self.release_data = ReleaseData()
        self.by_month = False
        self.raw_stat = False
        self.release_info_file_path = None

        self.show_stat(False)  # it performs resizing of self.root

        # center it last:
        self.root.eval('tk::PlaceWindow . center')  # without "withdraw/deiconify", it makes ugly blinking

        self.root.deiconify()  # show after center

    def run(self):
        self.root.mainloop()

    def show_raw(self):
        self.by_month = False
        self.raw_stat = True
        self.show_stat(False)

    def by_days_prev(self):
        to_date = self.cal.get_date()
        self.cal.set_date(to_date - datetime.timedelta(days=1))
        self.show_stat(False)

    def by_days_next(self):
        to_date = self.cal.get_date()
        self.cal.set_date(to_date + datetime.timedelta(days=1))
        self.show_stat(False)

    def by_days(self):
        today = datetime.date.today()
        self.cal.set_date(today)
        self.show_stat(False)

    def show_by_days(self):
        self.by_month = False
        self.raw_stat = False
        self.show_stat(False)

    def show_by_month(self):
        self.by_month = True
        self.raw_stat = False
        self.show_stat(False)

    def update_and_show_stat(self):
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
        # -------------------------------
        r_dao = ReleasesDao(self.ds)
        found = r_dao.find_by_name(r_name)
        if len(found) == 0:
            self.release_data = ReleaseData()
            self.release_data.r_name = r_name
            r_dao.create_release(self.release_data)
            self.ds.commit()
        else:
            self.release_data = found[0]
        return user, repo, tag_name

    @staticmethod
    def calc_diff(raw: []):
        res_raw = []
        res_diff = []
        for i in range(1, len(raw)):
            raw_curr = raw[i]
            raw_prev = raw[i - 1]
            if raw_prev[1] == 0:
                diff = 0  # in case when no history before, consider no downloads this day
            elif raw_curr[1] < raw_prev[1]:
                diff = 0
            else:
                diff = raw_curr[1] - raw_prev[1]
            res_diff.append((raw_curr[0], diff))
            res_raw.append((raw_curr[0], raw_curr[1]))
        return res_diff, res_raw

    @staticmethod
    def get_downloads_count(by_days_diff, curr_month_1st_day, curr_month_last_day):
        res = 0
        for d in by_days_diff:
            if curr_month_1st_day <= d[0] <= curr_month_last_day:
                res += d[1]
        return res

    def get_downloads(self, d_dao, date_begin, date_end):
        db_raw_by_days = d_dao.get_downloads_ordered_by_date_asc(self.release_data.r_id, f"{date_begin}", f"{date_end}")
        raw_by_days = self.get_raw_by_days(db_raw_by_days, date_begin, date_end)
        by_days_diff, by_days_raw = self.calc_diff(raw_by_days)
        return by_days_diff, by_days_raw

    def get_month_by_month(self, d_dao):
        today = datetime.date.today()
        downloads_max = -1
        downloads_data = []
        sum_for_period = 0
        curr_month_1st_day = datetime.date(year=today.year, month=today.month, day=1)
        date_begin = curr_month_1st_day - relativedelta.relativedelta(months=36)
        by_days_diff, by_days_raw = self.get_downloads(d_dao, date_begin, today)
        for _ in range(0, self.REPORT_RANGE):
            next_month_1st_day = curr_month_1st_day + relativedelta.relativedelta(months=1)
            curr_month_last_day = next_month_1st_day - datetime.timedelta(days=1)
            dt_downloads = self.get_downloads_count(by_days_diff, curr_month_1st_day, curr_month_last_day)
            sum_for_period += dt_downloads
            downloads_data.append((curr_month_last_day, dt_downloads))
            if dt_downloads > downloads_max:
                downloads_max = dt_downloads
            curr_month_1st_day = curr_month_1st_day - relativedelta.relativedelta(months=1)
        downloads_data = sorted(downloads_data, reverse=False)
        self.count.config(text=str(sum_for_period))
        return downloads_data, downloads_max, sum_for_period

    @staticmethod
    def get_raw_by_days(raw: [], start_date, end_date):
        raw_dict = {}
        for di in raw:
            raw_dict[di.d_date] = di
        res = []
        dt = start_date
        last_not_zero = 0
        while dt <= end_date:
            # f = "%Y-%m-%d"
            # dt = datetime.datetime.strptime(d[0], f).date()
            dts = dt.strftime("%Y-%m-%d")
            di = raw_dict.get(dts)
            if di:
                res.append((dt, di.d_downloads))
                last_not_zero = di.d_downloads
            else:
                res.append((dt, last_not_zero))
            dt = dt + datetime.timedelta(days=1)
        return res

    def get_day_by_day(self, d_dao):
        date_end = self.cal.get_date()
        date_begin = date_end - relativedelta.relativedelta(months=12)
        by_days_diff, by_days_raw = self.get_downloads(d_dao, date_begin, date_end)
        raw_dict = {}
        for di in by_days_raw:
            d_date = di[0]
            raw_dict[d_date] = di
        diff_dict = {}
        for di in by_days_diff:
            d_date = di[0]
            diff_dict[d_date] = di
        downloads_max = -1
        downloads_data = []
        sum_for_period = 0
        for days_before in range(self.REPORT_RANGE):
            dt = date_end - datetime.timedelta(days=days_before)
            if dt in diff_dict:
                sum_for_period += diff_dict[dt][1]  # SUM always by diff
                if self.raw_stat:
                    dt_downloads = raw_dict[dt][1]
                else:
                    dt_downloads = diff_dict[dt][1]
            else:
                dt_downloads = 0
            if dt_downloads > downloads_max:
                downloads_max = dt_downloads
            downloads_data.append((dt, dt_downloads))
        downloads_data = sorted(downloads_data, reverse=False)
        self.count.config(text=str(sum_for_period))
        return downloads_data, downloads_max, sum_for_period

    def get_chart_data(self):
        dao = DownloadsDao(self.ds)
        if self.by_month:
            return self.get_month_by_month(dao)
        else:
            return self.get_day_by_day(dao)

    def draw_chart(self, data, max_data_value):
        # https://stackoverflow.com/questions/35666573/use-tkinter-to-draw-a-specific-bar-chart
        y_stretch = (self.CHART_HEIGHT - 60) / max_data_value
        y_gap = 24
        x_stretch = 14
        x_width = 20
        x_gap = 10
        self.canvas.delete("all")
        for x, y_tuple in enumerate(data):
            dt, y = y_tuple
            if self.by_month:
                x_label = str(dt.month)  # .split("-")[1]
            else:
                x_label = str(dt.day)  # split("-")[2]
            x0 = x * x_stretch + x * x_width + x_gap
            y0 = self.CHART_HEIGHT - (y * y_stretch + y_gap)
            x1 = x * x_stretch + x * x_width + x_width + x_gap
            y1 = self.CHART_HEIGHT - y_gap
            hex_color = "#%02x%02x%02x" % (109, 170, 44)
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=hex_color)
            text_1 = self.canvas.create_text(x0, y0, anchor="nw", text=str(y))
            x_rect_offset = ((x1 - x0) / 2)
            self.center_align(text_1, x_rect_offset)
            if x_label == '1':
                text_2 = self.canvas.create_text(x0, y1 + 20, anchor="nw", text=str(x_label), fill='red')
            else:
                text_2 = self.canvas.create_text(x0, y1 + 20, anchor="nw", text=str(x_label))
            self.center_align(text_2, x_rect_offset)

            if x % 3 == 0:
                time.sleep(0.001)

    def build_chart(self):
        data, max_data_value, sum_for_period = self.get_chart_data()
        if max_data_value == 0:
            max_data_value = 1

        thr = Thread(target=self.draw_chart, args=(data, max_data_value,))
        thr.start()

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
        if self.by_month:
            return
        avg_for_period = round(sum_for_period / self.REPORT_RANGE, 1)
        if text:
            text += f"Past {self.REPORT_RANGE} days: {sum_for_period} downloads ({avg_for_period} a day)\n"
            self.label_release_info.config(text=text)

    def update_db(self, release_downloads_count):
        today = datetime.date.today()
        today = str(today)
        d_dao = DownloadsDao(self.ds)
        downloads_arr = d_dao.find_downloads(self.release_data.r_id, today)
        if len(downloads_arr) == 0:
            di = Downloads()
            di.r_id = self.release_data.r_id
            di.d_date = today
            di.d_downloads = release_downloads_count
            d_dao.create_download(di)
            self.ds.commit()
        else:
            if downloads_arr[0].d_downloads != release_downloads_count:
                downloads_arr[0].d_downloads = release_downloads_count
                d_dao.update_download(downloads_arr[0])
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
        return f'{release_info}\n\nThe 1st Release\n' \
               f'Published at {published_min}\n' \
               f'{days_from_start_date} days ago\n' \
               f'{total_downloads} downloads ({avg_downloads_a_day} a day)\n\n'

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
                       f"{release_downloads_count} downloads ({avg_downloads_a_day} a day)\n"
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
            messagebox.showerror(title='Error', message=f"{e}")


if __name__ == '__main__':
    app = MyApp()
    app.run()
