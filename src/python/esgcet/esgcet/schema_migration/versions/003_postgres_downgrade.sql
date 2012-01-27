--
-- revert tech notes addition
--

ALTER TABLE file_version
  DROP COLUMN tech_notes;

ALTER TABLE file_version
  DROP COLUMN tech_notes_title;

ALTER TABLE dataset_version
  DROP COLUMN tech_notes;

ALTER TABLE dataset_version
  DROP COLUMN tech_notes_title;
