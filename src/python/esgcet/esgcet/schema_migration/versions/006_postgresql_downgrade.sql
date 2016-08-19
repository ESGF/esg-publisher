--
-- Revert url size changes
--

update file_version set url=NULL where length(url)>255;

ALTER TABLE file_version
  ALTER url TYPE CHARACTER VARYING(255);