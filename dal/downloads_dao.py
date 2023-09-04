"""
Code generated by a tool. DO NOT EDIT.
https://sqldalmaker.sourceforge.net/
"""

from dal.downloads import Downloads


class DownloadsDao:

    def __init__(self, ds):
        self.ds = ds

    def create_download(self, p):
        """
        (C)RUD: downloads
        :param p: Downloads
        :return: int (the number of affected rows)
        """
        sql = """insert into downloads (r_id, d_date, d_downloads) values (?, ?, ?)"""

        return self.ds.exec_dml(sql, [p.r_id, p.d_date, p.d_downloads])

    def update_download(self, p):
        """
        CR(U)D: downloads
        :param p: Downloads
        :return: int (the number of affected rows)
        """
        sql = """update downloads set d_downloads=? where r_id=? and d_date=?"""

        return self.ds.exec_dml(sql, [p.d_downloads, p.r_id, p.d_date])

    def find_downloads(self, r_id, d_date):
        """
        :param r_id: int
        :param d_date: str
        :return: list[Downloads]
        """
        sql = """select * from downloads where r_id=? and d_date=?"""

        _res = []

        def _map_cb(row):
            _obj = Downloads()
            _obj.r_id = row["r_id"]  # t <- t [INFO] SQL-shortcut
            _obj.d_date = row["d_date"]  # t <- t
            _obj.d_downloads = row["d_downloads"]  # t <- t
            _res.append(_obj)

        self.ds.query_all_rows(sql, [r_id, d_date], _map_cb)

        return _res

    def get_downloads_ordered_by_date_asc(self, r_id, date_begin, date_end):
        """
        :param r_id: int
        :param date_begin: str
        :param date_end: str
        :return: list[Downloads]
        """
        sql = """select * from downloads 
                where r_id = ? 
                and strftime('%s', d_date) >= strftime('%s', ?) 
                and strftime('%s', d_date) <= strftime('%s', ?) 
                order by d_date asc"""

        _res = []

        def _map_cb(row):
            _obj = Downloads()
            _obj.r_id = row["r_id"]  # t <- q
            _obj.d_date = row["d_date"]  # t <- q
            _obj.d_downloads = row["d_downloads"]  # t <- q
            _res.append(_obj)

        self.ds.query_all_rows(sql, [r_id, date_begin, date_end], _map_cb)

        return _res
