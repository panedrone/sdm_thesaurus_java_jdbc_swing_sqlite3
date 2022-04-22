select * from downloads
where r_id = ?
and strftime('%s', d_date) <= strftime('%s', ?)
order by d_date desc
limit ?, ?