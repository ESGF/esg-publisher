--
-- Upgrade to increase standard_name size
--

ALTER TABLE standard_name
  ALTER name TYPE CHARACTER VARYING(255);

ALTER TABLE variable
  ALTER standard_name TYPE CHARACTER VARYING(255);
