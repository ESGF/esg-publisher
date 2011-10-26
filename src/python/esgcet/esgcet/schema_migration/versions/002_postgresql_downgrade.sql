--
-- Revert standard_name size changes
--

update variable set standard_name=NULL where length(standard_name)>128;
delete from standard_name where length(name)>128;

ALTER TABLE variable
  ALTER standard_name TYPE CHARACTER VARYING(128);

ALTER TABLE standard_name
  ALTER name TYPE CHARACTER VARYING(128);
