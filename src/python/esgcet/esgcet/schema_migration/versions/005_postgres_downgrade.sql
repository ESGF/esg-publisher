--
-- Revert location size changes
--

update file_version set location='value_too_long' where length(location)>255;

ALTER TABLE file_version
  ALTER location TYPE CHARACTER VARYING(255);