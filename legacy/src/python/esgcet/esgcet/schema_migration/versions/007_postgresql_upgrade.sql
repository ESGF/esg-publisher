--
-- Upgrade to add is_target_variable boolean to file_variable
--

ALTER TABLE file_variable
  ADD COLUMN is_target_variable BOOLEAN;
