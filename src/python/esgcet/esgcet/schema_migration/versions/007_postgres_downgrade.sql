--
-- revert addition of is_target_variable
--

ALTER TABLE file_variable
  DROP COLUMN is_target_variable;
