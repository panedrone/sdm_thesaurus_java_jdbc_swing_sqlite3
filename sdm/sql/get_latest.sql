select * from downloads
where r_id = ?
order by d_date DESC
limit ?, ?