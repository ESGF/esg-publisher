--
-- Upgrade to add citation and PID
--

ALTER TABLE dataset_version
  ADD COLUMN citation_url CHARACTER VARYING(255);

ALTER TABLE dataset_version
  ADD COLUMN pid CHARACTER VARYING(255);
