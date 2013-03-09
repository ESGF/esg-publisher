--
-- Upgrade to improve esgunpublish performance
--

CREATE INDEX file_variable_variable_id_index ON file_variable USING btree (variable_id);
CREATE INDEX file_variable_file_id_index on file_variable USING btree (file_id);
ANALYZE file_variable;

CREATE INDEX dataset_file_version_id_index ON dataset_file_version USING btree (file_version_id);
ANALYZE dataset_file_version;

CREATE INDEX file_version_file_id_index ON file_version USING btree (file_id);
ANALYZE file_version;
