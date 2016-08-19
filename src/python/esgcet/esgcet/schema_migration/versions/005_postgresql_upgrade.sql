--
-- Upgrade to increase location size
--

ALTER TABLE file_version
  ALTER location TYPE TEXT;