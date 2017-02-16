--
-- revert Citation and PID creation
--

ALTER TABLE dataset_version
  DROP COLUMN citation_url;

ALTER TABLE dataset_version
  DROP COLUMN pid;
