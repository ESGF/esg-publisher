--
-- Revert location size changes
--

update catalog set location='value_too_long' length(location)>255;

ALTER TABLE catalog
  ALTER location TYPE CHARACTER VARYING(255);