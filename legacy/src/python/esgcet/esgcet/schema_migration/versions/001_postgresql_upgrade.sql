--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: catalog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE catalog (
    dataset_name character varying(255) NOT NULL,
    version integer NOT NULL,
    location character varying(255) NOT NULL,
    rootpath character varying(255)
);


--
-- Name: dataset; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dataset (
    id integer NOT NULL,
    name character varying(255),
    project character varying(64),
    model character varying(64),
    experiment character varying(64),
    run_name character varying(64),
    calendar character varying(32),
    aggdim_name character varying(64),
    aggdim_units character varying(64),
    status_id character varying(64),
    offline boolean,
    master_gateway character varying(64)
);


--
-- Name: dataset_attr; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dataset_attr (
    dataset_id integer NOT NULL,
    name character varying(64) NOT NULL,
    value text NOT NULL,
    datatype character(1) NOT NULL,
    length integer NOT NULL,
    is_category boolean,
    is_thredds_category boolean
);


--
-- Name: dataset_file_version; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dataset_file_version (
    dataset_version_id integer,
    file_version_id integer
);


--
-- Name: dataset_status; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dataset_status (
    id integer NOT NULL,
    datetime timestamp without time zone,
    object_id integer,
    level integer,
    module integer,
    status text
);


--
-- Name: dataset_version; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE dataset_version (
    id integer NOT NULL,
    dataset_id integer,
    version integer,
    name character varying(255),
    creation_time timestamp without time zone,
    comment text
);


--
-- Name: download; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE download (
    userid character varying(64),
    url character varying(255)
);


--
-- Name: event; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE event (
    id integer NOT NULL,
    datetime timestamp without time zone NOT NULL,
    object_id integer,
    object_name character varying(255) NOT NULL,
    object_version integer,
    event integer
);


--
-- Name: experiment; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE experiment (
    name character varying(64) NOT NULL,
    project character varying(64) NOT NULL,
    description text
);


--
-- Name: file; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE file (
    id integer NOT NULL,
    dataset_id integer NOT NULL,
    base character varying(255) NOT NULL,
    format character varying(16)
);


--
-- Name: file_attr; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE file_attr (
    file_id integer NOT NULL,
    name character varying(64) NOT NULL,
    value text NOT NULL,
    datatype character(1) NOT NULL,
    length integer NOT NULL
);


--
-- Name: file_var_attr; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE file_var_attr (
    filevar_id integer NOT NULL,
    name character varying(64) NOT NULL,
    value text NOT NULL,
    datatype character(1) NOT NULL,
    length integer NOT NULL
);


--
-- Name: file_variable; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE file_variable (
    id integer NOT NULL,
    file_id integer NOT NULL,
    variable_id integer,
    short_name character varying(255) NOT NULL,
    long_name character varying(255),
    aggdim_first double precision,
    aggdim_last double precision,
    aggdim_units character varying(64),
    coord_range character varying(32),
    coord_type character varying(8),
    coord_values text
);


--
-- Name: file_version; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE file_version (
    id integer NOT NULL,
    file_id integer,
    version integer,
    location character varying(255) NOT NULL,
    size bigint,
    checksum character varying(64),
    checksum_type character varying(32),
    publication_time timestamp without time zone,
    tracking_id character varying(64),
    mod_time double precision,
    url character varying(255)
);


--
-- Name: filevar_dimension; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE filevar_dimension (
    filevar_id integer NOT NULL,
    name character varying(64) NOT NULL,
    length integer NOT NULL,
    seq integer NOT NULL
);


--
-- Name: las_catalog; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE las_catalog (
    dataset_name character varying(255) NOT NULL,
    location character varying(255) NOT NULL
);


--
-- Name: model; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE model (
    name character varying(64) NOT NULL,
    project character varying(64) NOT NULL,
    url character varying(128),
    description text
);


--
-- Name: project; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE project (
    name character varying(64) NOT NULL,
    description character varying(64)
);


--
-- Name: standard_name; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE standard_name (
    name character varying(128) NOT NULL,
    units character varying(64),
    amip character varying(64),
    grib character varying(64),
    description text
);


--
-- Name: var_attr; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE var_attr (
    variable_id integer NOT NULL,
    name character varying(64) NOT NULL,
    value text NOT NULL,
    datatype character(1) NOT NULL,
    length integer NOT NULL
);


--
-- Name: var_dimension; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE var_dimension (
    variable_id integer NOT NULL,
    name character varying(64) NOT NULL,
    length integer NOT NULL,
    seq integer NOT NULL
);


--
-- Name: variable; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE variable (
    id integer NOT NULL,
    dataset_id integer,
    short_name character varying(255),
    long_name character varying(255),
    standard_name character varying(128),
    vertical_granularity character varying(64),
    grid integer,
    aggdim_first double precision,
    aggdim_last double precision,
    units character varying(64),
    has_errors boolean,
    eastwest_range character varying(64),
    northsouth_range character varying(64),
    updown_range character varying(64),
    updown_values text
);


--
-- Name: catalog_version_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE catalog_version_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: catalog_version_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE catalog_version_seq OWNED BY catalog.version;


--
-- Name: dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dataset_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: dataset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dataset_id_seq OWNED BY dataset.id;


--
-- Name: dataset_status_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dataset_status_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: dataset_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dataset_status_id_seq OWNED BY dataset_status.id;


--
-- Name: dataset_version_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dataset_version_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: dataset_version_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dataset_version_id_seq OWNED BY dataset_version.id;


--
-- Name: event_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE event_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: event_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE event_id_seq OWNED BY event.id;


--
-- Name: file_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE file_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: file_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE file_id_seq OWNED BY file.id;


--
-- Name: file_variable_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE file_variable_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: file_variable_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE file_variable_id_seq OWNED BY file_variable.id;


--
-- Name: file_version_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE file_version_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: file_version_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE file_version_id_seq OWNED BY file_version.id;


--
-- Name: variable_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE variable_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: variable_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE variable_id_seq OWNED BY variable.id;


--
-- Name: version; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE catalog ALTER COLUMN version SET DEFAULT nextval('catalog_version_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE dataset ALTER COLUMN id SET DEFAULT nextval('dataset_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE dataset_status ALTER COLUMN id SET DEFAULT nextval('dataset_status_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE dataset_version ALTER COLUMN id SET DEFAULT nextval('dataset_version_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE event ALTER COLUMN id SET DEFAULT nextval('event_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE file ALTER COLUMN id SET DEFAULT nextval('file_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE file_variable ALTER COLUMN id SET DEFAULT nextval('file_variable_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE file_version ALTER COLUMN id SET DEFAULT nextval('file_version_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE variable ALTER COLUMN id SET DEFAULT nextval('variable_id_seq'::regclass);


--
-- Name: catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY catalog
    ADD CONSTRAINT catalog_pkey PRIMARY KEY (dataset_name, version);


--
-- Name: dataset_attr_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dataset_attr
    ADD CONSTRAINT dataset_attr_pkey PRIMARY KEY (dataset_id, name);


--
-- Name: dataset_name_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dataset
    ADD CONSTRAINT dataset_name_key UNIQUE (name);


--
-- Name: dataset_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dataset
    ADD CONSTRAINT dataset_pkey PRIMARY KEY (id);


--
-- Name: dataset_status_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dataset_status
    ADD CONSTRAINT dataset_status_pkey PRIMARY KEY (id);


--
-- Name: dataset_version_name_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dataset_version
    ADD CONSTRAINT dataset_version_name_key UNIQUE (name);


--
-- Name: dataset_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY dataset_version
    ADD CONSTRAINT dataset_version_pkey PRIMARY KEY (id);


--
-- Name: event_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY event
    ADD CONSTRAINT event_pkey PRIMARY KEY (id);


--
-- Name: experiment_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY experiment
    ADD CONSTRAINT experiment_pkey PRIMARY KEY (name, project);


--
-- Name: file_attr_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY file_attr
    ADD CONSTRAINT file_attr_pkey PRIMARY KEY (file_id, name);


--
-- Name: file_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY file
    ADD CONSTRAINT file_pkey PRIMARY KEY (id);


--
-- Name: file_var_attr_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY file_var_attr
    ADD CONSTRAINT file_var_attr_pkey PRIMARY KEY (filevar_id, name);


--
-- Name: file_variable_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY file_variable
    ADD CONSTRAINT file_variable_pkey PRIMARY KEY (id);


--
-- Name: file_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY file_version
    ADD CONSTRAINT file_version_pkey PRIMARY KEY (id);


--
-- Name: filevar_dimension_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY filevar_dimension
    ADD CONSTRAINT filevar_dimension_pkey PRIMARY KEY (filevar_id, name);


--
-- Name: las_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY las_catalog
    ADD CONSTRAINT las_catalog_pkey PRIMARY KEY (dataset_name);


--
-- Name: model_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY model
    ADD CONSTRAINT model_pkey PRIMARY KEY (name, project);


--
-- Name: project_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY project
    ADD CONSTRAINT project_pkey PRIMARY KEY (name);


--
-- Name: standard_name_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY standard_name
    ADD CONSTRAINT standard_name_pkey PRIMARY KEY (name);


--
-- Name: var_attr_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY var_attr
    ADD CONSTRAINT var_attr_pkey PRIMARY KEY (variable_id, name);


--
-- Name: var_dimension_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY var_dimension
    ADD CONSTRAINT var_dimension_pkey PRIMARY KEY (variable_id, name);


--
-- Name: variable_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY variable
    ADD CONSTRAINT variable_pkey PRIMARY KEY (id);


--
-- Name: datasetversion_index; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE UNIQUE INDEX datasetversion_index ON dataset_version USING btree (name);


--
-- Name: filevar_index; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE UNIQUE INDEX filevar_index ON file_variable USING btree (file_id, variable_id);


--
-- Name: ix_event_datetime; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX ix_event_datetime ON event USING btree (datetime);


--
-- Name: dataset_attr_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dataset_attr
    ADD CONSTRAINT dataset_attr_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES dataset(id);


--
-- Name: dataset_experiment_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dataset
    ADD CONSTRAINT dataset_experiment_fkey FOREIGN KEY (experiment, project) REFERENCES experiment(name, project);


--
-- Name: dataset_file_version_dataset_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dataset_file_version
    ADD CONSTRAINT dataset_file_version_dataset_version_id_fkey FOREIGN KEY (dataset_version_id) REFERENCES dataset_version(id);


--
-- Name: dataset_file_version_file_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dataset_file_version
    ADD CONSTRAINT dataset_file_version_file_version_id_fkey FOREIGN KEY (file_version_id) REFERENCES file_version(id);


--
-- Name: dataset_model_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dataset
    ADD CONSTRAINT dataset_model_fkey FOREIGN KEY (model, project) REFERENCES model(name, project);


--
-- Name: dataset_status_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dataset_status
    ADD CONSTRAINT dataset_status_object_id_fkey FOREIGN KEY (object_id) REFERENCES dataset(id);


--
-- Name: dataset_version_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dataset_version
    ADD CONSTRAINT dataset_version_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES dataset(id);


--
-- Name: event_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY event
    ADD CONSTRAINT event_object_id_fkey FOREIGN KEY (object_id) REFERENCES dataset(id);


--
-- Name: experiment_project_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY experiment
    ADD CONSTRAINT experiment_project_fkey FOREIGN KEY (project) REFERENCES project(name);


--
-- Name: file_attr_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY file_attr
    ADD CONSTRAINT file_attr_file_id_fkey FOREIGN KEY (file_id) REFERENCES file(id);


--
-- Name: file_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY file
    ADD CONSTRAINT file_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES dataset(id);


--
-- Name: file_var_attr_filevar_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY file_var_attr
    ADD CONSTRAINT file_var_attr_filevar_id_fkey FOREIGN KEY (filevar_id) REFERENCES file_variable(id);


--
-- Name: file_variable_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY file_variable
    ADD CONSTRAINT file_variable_file_id_fkey FOREIGN KEY (file_id) REFERENCES file(id);


--
-- Name: file_variable_variable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY file_variable
    ADD CONSTRAINT file_variable_variable_id_fkey FOREIGN KEY (variable_id) REFERENCES variable(id);


--
-- Name: file_version_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY file_version
    ADD CONSTRAINT file_version_file_id_fkey FOREIGN KEY (file_id) REFERENCES file(id);


--
-- Name: filevar_dimension_filevar_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY filevar_dimension
    ADD CONSTRAINT filevar_dimension_filevar_id_fkey FOREIGN KEY (filevar_id) REFERENCES file_variable(id);


--
-- Name: model_project_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY model
    ADD CONSTRAINT model_project_fkey FOREIGN KEY (project) REFERENCES project(name);


--
-- Name: var_attr_variable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY var_attr
    ADD CONSTRAINT var_attr_variable_id_fkey FOREIGN KEY (variable_id) REFERENCES variable(id);


--
-- Name: var_dimension_variable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY var_dimension
    ADD CONSTRAINT var_dimension_variable_id_fkey FOREIGN KEY (variable_id) REFERENCES variable(id);


--
-- Name: variable_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY variable
    ADD CONSTRAINT variable_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES dataset(id);


--
-- Name: variable_standard_name_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY variable
    ADD CONSTRAINT variable_standard_name_fkey FOREIGN KEY (standard_name) REFERENCES standard_name(name);
