--
-- Upgrade to add tech notes
--

ALTER TABLE file_version
  ADD COLUMN tech_notes CHARACTER VARYING(255);

ALTER TABLE file_version
  ADD COLUMN tech_notes_title CHARACTER VARYING(255);

ALTER TABLE dataset_version
  ADD COLUMN tech_notes CHARACTER VARYING(255);

ALTER TABLE dataset_version
  ADD COLUMN tech_notes_title CHARACTER VARYING(255);
