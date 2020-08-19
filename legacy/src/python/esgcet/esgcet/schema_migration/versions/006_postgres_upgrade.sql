--
-- Upgrade to increase url size
--

ALTER TABLE file_version
  ALTER url TYPE TEXT;