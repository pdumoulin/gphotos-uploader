SELECT *
FROM uploads
WHERE local_dir = :local_dir
AND album_id = :album_id;
