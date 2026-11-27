import esgvoc.api as ev
from xnetcdf import Dataset
from esgcet.util.mapfile import ESGPubMapConv
from esgcet.stac.stac_client import EGITransactionClient
from datetime import datetime
import json
import yaml
import requests
import re
from urllib.parse import urljoin

from esgcet.util import logger
from esgcet.vocab.extractors import get_geo

log = logger.ESGPubLogger()

DEBUG=True

def check_url(url: str) -> bool:
    resp = requests.get(url)
    return str(resp.status_code) == '200'


class ESGCatalogProperty:
    description="Catalog Property Object to hold attributes of a property."

    def __init__(
            self, 
            catalog_field_name: str,
            value_type: str,
            required: bool,
            key: str,
            log_kwargs: dict):

        log_kwargs = log_kwargs or {}
        self.publog = log.return_logger("ESGCatalogProperty", **log_kwargs)

        self.catalog_field_name = catalog_field_name
        self.value_type = value_type
        self.required = required
        self.key = key

class ESGVocabValue:

    def __init__(self, 
            source_collection: str,
            catalog_field_name: str,
            cv: bool,
            value_type: str,
            catalog_required: bool,
            cv_key: str,
            log_kwargs: dict | None = None):
        # Attribute spec and catalog_spec for a single entry
        # All properties remain public

        self.log_kwargs  = log_kwargs or {}
        self.publog = log.return_logger("ESGVocabValue", **self.log_kwargs)

        self.source_collection = source_collection
        self.cv = cv

        self.catalog_fields = []

        self.add_catalog_field(
            catalog_field_name,
            value_type,
            catalog_required,
            cv_key
        )

        self.netcdf_field_names = []

    def add_catalog_field(self, 
            catalog_field_name: str,
            value_type: str,
            required: bool,
            key: str):
        """
        Create catalog_property object to track this info.
        """
        self.publog.debug(f'Adding STAC {catalog_field_name} to {self.source_collection}')
        self.catalog_fields.append(
            ESGCatalogProperty(
                catalog_field_name,
                value_type,
                required,
                key,
                log_kwargs=self.log_kwargs
            ))

    def add_netcdf_field_name(self, netcdf_field_name: str):

        self.publog.debug(f'Adding netcdf {netcdf_field_name} to {self.source_collection}')
        self.netcdf_field_names.append(netcdf_field_name)

class ESGVocabMapper:

    def __init__(self, 
            project: str, 
            netcdf_source: dict,
            netcdf_path: str,
            log_kwargs: dict | None = None,
            overrides: dict | None = None,
            exclusions: list | None = None,
            json_map: dict | None = None):
        """
        Assemble vocabulary mappings based on the given project.

        Any hardcoded things should be kept here for vocabularies.
        """

        self.log_kwargs  = log_kwargs or {}
        self.publog = log.return_logger("ESGVocabMapper", **self.log_kwargs)

        self.project       = project
        self.netcdf_source = netcdf_source
        self.json_source   = json_map
        self.netcdf_path   = netcdf_path

        self.publog.info("Assembling mappings from esgvoc...")

        self.cv_mappings = self._extract_esgvoc()

        self.overrides = overrides
        self.exclusions = exclusions or []

        self.publog.info("Assembling mappings from file/dir structure...")
        self.netcdf_dir_map, self.netcdf_file_map = self._extract_netcdf()

    def _extract_netcdf(self):
        """
        Extract parts from netcdf file/dir components"""

        self.publog.debug(f'NetCDF file: {self.netcdf_path.split("/")[-1]}')

        netcdf_file_parts = self.netcdf_path.split('/')[-1].split(
            ev.projects.get_project(self.project).drs_specs['file_name'].separator
        )
        netcdf_file_parts[-1] = netcdf_file_parts[-1].split(
            ev.projects.get_project(self.project).drs_specs['file_name'].properties['extension_separator']
        )[0]

        netcdf_dir_parts  = self.netcdf_path.split('/')[1:-1]

        parts = ev.projects.get_project(self.project).drs_specs['directory'].parts
        offset = len(netcdf_dir_parts) - len(parts)

        self.publog.debug(f'Directory: {"/".join(netcdf_dir_parts[offset:])}')

        netcdf_dir_map = {}
        for index, f in enumerate(parts):
            netcdf_dir_map[str(f)] = netcdf_dir_parts[index+offset]

        netcdf_file_map = {}
        for index, f in enumerate(ev.projects.get_project(self.project).drs_specs['file_name'].parts):
            netcdf_file_map[str(f)] = netcdf_file_parts[index]

        return netcdf_dir_map, netcdf_file_map

    def _extract_esgvoc(self):
        """
        Extract esgvoc mappings form project"""

        mappings = {}

        ev_project = ev.projects.get_project(self.project)

        dataset_props = ev_project.catalog_specs.dataset_properties
        attrs = ev_project.attr_specs

        self.publog.info('Assembling dataset properties...')

        for f in dataset_props:

            # Same value if either one is None, otherwise separate values.
            source             = f.source_collection or f.catalog_field_name
            catalog_field_name = f.catalog_field_name or f.source_collection

            is_cv = (f.source_collection is not None)
            if not is_cv:
                source = '.' + source
                self.publog.debug(f'Adding "{source}" non-vocab term')
            else:
                self.publog.debug(f'Adding "{source}" vocabulary')

            added = False
            if source in mappings:
                if is_cv == mappings[source].cv:
                    mappings[source].add_catalog_field(
                        catalog_field_name,
                        f.catalog_field_value_type or 'string',
                        f.is_required,
                        f.source_collection_key)

                    self.publog.debug(
                        f'Adding "{catalog_field_name}" to existing '
                        f'vocabulary "{source}"')
                    added = True
            if not added:

                facet = ESGVocabValue(
                    source_collection  = source,
                    catalog_field_name = catalog_field_name,
                    cv=(f.source_collection is not None),
                    value_type=f.catalog_field_value_type or 'string',
                    catalog_required=f.is_required,
                    cv_key=f.source_collection_key,
                    log_kwargs=self.log_kwargs
                )

                mappings[source] = facet

        self.publog.info('Matching to attributes...')

        for f in attrs:

            # Same value if either one is None, otherwise separate values.
            source          = f.source_collection or f.attr_field_name
            attr_field_name = f.attr_field_name or f.source_collection

            is_cv = (f.source_collection is not None)
            if not is_cv:
                source = '.' + source
                self.publog.debug(f'Adding "{source}" non-vocab term')

            if source not in mappings:
                # Attribute is defined but does not feed into the catalog
                self.publog.debug(f'"{source}" ignored - not in catalog')
                continue

            facet = mappings[source]


            # Only add this attribute it it doesn't have a source_collection_key
            if not f.source_collection_key:
                self.publog.debug(f'"{attr_field_name}" added from netcdf')
                facet.add_netcdf_field_name(attr_field_name)
            else:
                self.publog.debug(f'"{attr_field_name}" - will pull from CVs')

        return mappings

    def _extract_from_source(
            self, 
            extract_label: str | list, 
            source_cv: str,
            source_type: str,
            is_array: bool = False):
        """
        Override with json source if present.
        """

        if self.json_source:
            for label in extract_label:
                if label in self.json_source:
                    self.publog.debug(
                        f'Extracting "{label}" from user-provided JSON'
                    )
                    return self.validate_term(
                        self.project,
                        source_cv,
                        self.json_source.get(label),
                        source_type,
                        is_array=is_array
                    )

        if source_type == 'NetCDF Attributes':
            return self._extract_from_netcdf(extract_label, source_cv, is_array=is_array)
        else:
            return self._extract_from_fp(extract_label[0], is_array=is_array)

    def _extract_from_netcdf(self, extractors: list, source: str, is_array: bool = False) -> str:
        """
        Extract attribute from netcdf source
        """

        sourced = False
        extract = 0
        while not sourced:

            param = self.netcdf_source.get(extractors[extract],None)
            extract += 1

            if param:
                sourced = True
            elif extract >= len(extractors):
                param = None
                sourced = True

        return self.validate_term(
            self.project,
            source,
            param,
            'NetCDF Attributes',
            is_array=is_array)

    def _extract_from_fp(self, f_label: str, is_array: bool = False) -> str | None:
        """
        Extract a facet from the netcdf directory/file maps
        """

        if f_label in self.netcdf_dir_map:
            return self.validate_term(
                self.project,
                f_label,
                self.netcdf_dir_map[f_label],
                'Dir Structure',
                is_array=is_array)
        if f_label in self.netcdf_file_map:
            return self.validate_term(
                self.project,
                f_label,
                self.netcdf_file_map[f_label],
                'File Structure',
                is_array=is_array)
        return None

    def _extract_array(self, value: str) -> list:

        if ' ' not in value and ';' not in value:
            return [value]

        value = [v for v in value.replace(';',' ').split(' ') if v]
        return value

    def _assemble_stac_property(
            self,
            netcdf_extract: list,
            catalog_field: ESGCatalogProperty,
            valuelabel: ESGVocabValue,
            param: str | None = None):

        value = None
        is_array = (catalog_field.value_type == 'string_array')

        # NetCDF attributes using the same source collection
        # Catalog fields extracted by matching names.
        if len(netcdf_extract) > 1:
            ext = [e for e in netcdf_extract if e == catalog_field.catalog_field_name]
            param = self._extract_from_source(ext, valuelabel.source_collection, "NetCDF Attributes", is_array=is_array)
            self.publog.debug(
                f'Catalog field "{catalog_field.catalog_field_name}" '
                f'extracted value "{param}" from netcdf')

        if param is None:
            fp_extract = catalog_field.catalog_field_name
            if catalog_field.key is not None:
                fp_extract = valuelabel.source_collection

            param = self._extract_from_source([fp_extract], fp_extract, "File/Dir Structure", is_array=is_array)
            self.publog.debug(
                f'Catalog field "{fp_extract}" '
                f'extracted value "{param}" from file/dir')

        if param is None:
            value = None
        elif catalog_field.key is None:
            value = param
        else:
            term = ev.get_term_in_collection(
                project_id=self.project,
                collection_id=valuelabel.source_collection,
                term_id=param.lower()
            )
            if term:
                value = getattr(term, catalog_field.key, None)
                self.publog.debug(
                    f'Catalog field "{catalog_field.catalog_field_name}" '
                    f'extracted value "{value}" from CV {catalog_field.key}')

        if value is None:
            if catalog_field.required:

                if catalog_field.catalog_field_name in self.overrides:
                    value = self.overrides.get(catalog_field.catalog_field_name)
                    self.publog.warning(
                        f'Using user-provided override value "{value}" '
                        f'for property "{catalog_field.catalog_field_name}"'
                    )
                else:

                    value = 'MISSING'
                    self.publog.error(
                        f'Property {catalog_field.catalog_field_name} could not be sourced'
                        ' where it is required.'
                    )

        if value is None:
            return None

        # Handle arrayed/non-arrayed properties
        if 'array' not in catalog_field.value_type and isinstance(value, list):
            if len(value) > 1:
                self.publog.error(
                    f'Non-array property "{catalog_field.catalog_field_name}"'
                    f' given value "{value}"'
                )
                value = "TOO_MANY_VALUES"
            value = value[0]

        return {f'{self.project}:{catalog_field.catalog_field_name}':value}

    def validate_term(self, project: str, source: str, term: str, extract: str, is_array: bool = False) -> str:
        """
        Use ESGVOC to validate an extracted term.
        """

        if source.startswith('.'):
            return term

        # Handle validating array-based terms
        if is_array:
            value = self._extract_array(term)
            for v in value:
                self.validate_term(project, source, v, extract, is_array=False)
            return value

        if term is None:
            self.publog.debug(
                f'Skip validating "{term}" for collection "{source}" '
                f'within project "{project}"'
                f' - sourced from {extract}'
            )
            return term

        if not ev.valid_term_in_collection(
            value=term, 
            project_id=project, 
            collection_id=source):

            self.publog.warning(
                f'Term "{term}" for collection "{source}" '
                f'not valid within project "{project}"'
                f' - sourced from {extract}'
            )
            return None
        else:
            self.publog.debug(
                'VALID: '
                f'Term "{term}" for collection "{source}" '
                f'within project "{project}"'
                f' - sourced from {extract}')
            
        return term

    def get_dataset_id(self):
        """
        Assemble the dataset ID according to ESGVOC"""

        dataset_id = []

        separator = str(ev.projects.get_project(self.project).drs_specs['dataset_id'].separator)

        self.publog.info('Assembling Dataset ID...')

        for f in ev.projects.get_project(self.project).drs_specs['dataset_id'].parts:

            f_label = str(f)
            self.publog.debug(f'Identifying "{f_label}" source')

            param = self._extract_from_source([f_label], f_label, "File/Dir Structure")
            
            if param is None and f_label not in self.cv_mappings:
                raise ValueError(
                    f'Property {f_label} has no apparent source'
                )

            if param is None:
                netcdf_extract = self.cv_mappings[f_label].netcdf_field_names
                param = self._extract_from_source(netcdf_extract, f_label, "NetCDF Attributes")
                self.publog.debug(f'Sourced "{f_label}" from netcdf')
            else:
                self.publog.debug(f'Sourced "{f_label}" from file/dir')

            dataset_id.append(param)

        return separator.join(dataset_id)

    def get_stac_properties(self):
        """
        Assemble the STAC properties according to collected catalog_specs
        """

        self.publog.info('Assembling STAC properties...')

        properties = {}
        for valuelabel in self.cv_mappings.values():

            param = None
            netcdf_extract = valuelabel.netcdf_field_names
            if len(netcdf_extract) == 1:
                is_array = (valuelabel.catalog_fields[0].value_type == 'string_array')
                param = self._extract_from_source(netcdf_extract, valuelabel.source_collection, "NetCDF Attributes", is_array=is_array)
            
            for catalog_field in valuelabel.catalog_fields:

                if catalog_field.catalog_field_name in self.exclusions and not catalog_field.required:
                    self.publog.warning(
                        f'Skipping property "{catalog_field.catalog_field_name}"')
                    continue

                property = self._assemble_stac_property(netcdf_extract, catalog_field, valuelabel, param=param)
                if property:
                    properties.update(property)

        return properties

    def get_directory_structure(self):
        """
        Get the directory structure from the given parts"""

        return '/'.join(list(self.netcdf_dir_map.values()))

    def display_mappings(self):
        """
        Helpful display of mapped properties"""

        for cv, value in self.cv_mappings.items():
            print('---------------------')
            if value.cv:
                print(f'CV: {cv}')
            else:
                print(f'Unaffiliated: {cv}')


            print()
            for ncattr in value.netcdf_field_names:
                print(f'NetCDF source: {ncattr}')
            print()

            for prop in value.catalog_fields:
                if prop.required:
                    print(f'STAC: {prop.catalog_field_name} (REQUIRED)')
                else:
                    print(f'STAC: {prop.catalog_field_name}')
                print(f'> {prop.value_type}')
                if prop.key:
                    print(f'> Sourced from {cv}.{prop.key}')
                print()

            print('---------------------')
            print()

class ESGNetcdfAssembler:

    def __init__(
            self, 
            mapfile: str, 
            stac_config_file: str,
            collection: str | None = None,
            project: str | None = None,
            link_info: dict | None = None,
            save_stac: bool = False,
            dry_run: bool = False,
            verbose: bool = False,
            silent: bool = False,
            jsonfile: str | dict | None = None):
        """
        Initialise Assembly from a map file
        """

        self.config = self._load_cfg_file(stac_config_file)

        # Handle JSON provided mappings
        if isinstance(jsonfile, str):
            with open(jsonfile) as f:
                self.json_map = json.load(f)
        elif isinstance(jsonfile, dict):
            self.json_map = jsonfile
        else:
            self.json_map = None

        self.save_stac = save_stac
        self.dry_run = dry_run

        self.config['verbose'] = verbose or self.config.get('verbose')
        self.config['silent'] = silent or self.config.get('silent')

        self.publog = log.return_logger("ESGNetcdfAssembler", 
            **{
                'verbose': self.config.get('verbose'),
                'silent': self.config.get('silent')
        })

        if self.config['access'] == 'HTTPS':
            self.access = {
                'root':'https://',
                'type':'application/netcdf',
                'description':'HTTPServer Link',
                'protocol':'https',
                'access':['HTTPServer']
            }
        else:
            self.access = {}

        self.stac_api  = self.config.get('stac_api')
        self.data_node = self.config.get('data_node')

        self.collection = collection or self.config.get('collection')
        self.project    = project or self.collection.lower()

        self.link_info  = link_info or {}
        self.overrides  = self.config.get('overrides') or {}
        self.exclusions = self.config.get('exclusions') or []

        self.geo = {}

        if not ev.get_project(project_id=self.project):
            raise ValueError(
                f'ESGVOC Project "{self.project}" not valid - options '
                f'are {", ".join(ev.get_all_projects())}'
            )
        collections = self.get_stac_collections()
        if self.collection not in collections:
            raise ValueError(
                f'STAC Collection "{self.collection}" not valid - options '
                f'are {", ".join(collections)}'
            )

        mapconv = ESGPubMapConv(mapfile, project=project)
        mapconv.mapfilerun(mountpoints=self.config.get('mountpoints',None))

        self.mapfileinfo = mapconv.parse_map_arr()

        self.ncattrs = {}

    def get_stac_collections(self) -> list:
        """
        Gets the set of STAC collections known to the API
        """
        return ['CMIP7','obs4MIPs'] #[c['id'] for c in requests.get(f'{self.stac_api}/collections').json()['collections']]

    def _load_cfg_file(self, cfg_file: str) -> dict:
        """
        Load configuration details from config file

        - stac_api
        - data_node
        - mountpoints (optional)
        - data roots
        - verbose
        - silent
        - test
        - project
        - access

        """
        with open(cfg_file) as f:
            cfg = yaml.safe_load(f)
        return cfg

    def file_to_remote(self, file: str) -> str:
        """
        Map local file using remote endpoint config"""

        for root, rep in self.config['data_roots'].items():
            if root in file:
                file = file.replace(root, rep)

        data_node = f'esgf.{self.data_node}'
        if 'OVERRIDE' in self.data_node:
            data_node = self.data_node.split(':')[1]

        return self.access['root'] + urljoin(data_node,file)

    def file_to_local(self, file: str, dir_struct: str) -> str:
        """
        Map local file to expected filepath segment"""

        return f'{dir_struct}/{file.split("/")[-1]}'

    def geo_info_for_file(self, file):

        with Dataset(file) as ds:
            record = get_geo(ds, self.publog)

        # Combine spatial information
        for d in ['west_degrees','south_degrees']:
            if d in record:
                val = record.pop(d)
                if val < self.geo.get(d,999):
                    self.geo[d] = val
        for d in ['north_degrees','east_degrees']:
            if d in record:
                val = record.pop(d)
                if val > self.geo.get(d,-999):
                    self.geo[d] = val

        # Combine temporal information
        if 'datetime_start' in record:
            ds = record.pop('datetime_start')
            current = self.geo.get('datetime_start')
            if not current:
                self.geo['datetime_start'] = ds
            elif ds < self.geo['datetime_start']:
                self.geo['datetime_start'] = ds

        if 'datetime_end' in record:
            de = record.pop('datetime_end')
            current = self.geo.get('datetime_end')
            if not current:
                self.geo['datetime_end'] = de
            elif de > self.geo['datetime_end']:
                self.geo['datetime_end'] = de

        # Carry over any other properties not handled above.
        self.geo.update(record)

    def handle_spatial(self):
        """
        Apply spatial limiting, assemble coordinates, bbox."""

        west_degrees = float(self.geo.get("west_degrees", -180.0))
        south_degrees = float(self.geo.get("south_degrees", -90.0))
        east_degrees = float(self.geo.get("east_degrees", 180.0))
        north_degrees = float(self.geo.get("north_degrees", 90.0))

        # STAC needs longitude in range [-180, 180], but CF might use [0, 360)

        if abs(east_degrees - west_degrees - 360) < 1e-3:
            # represent any global range (e.g. 0 to 360 or -180 to 180 in the data)
            # as -180 to 180
            west_degrees, east_degrees = -180., 180.
        else:
            # otherwise force each value separately to range [-180, 180) (for west)
            # or (-180, 180] (for east)
            west_degrees = (west_degrees + 180) % 360 - 180
            east_degrees = (east_degrees + 180) % 360 - 180

            if east_degrees == -180.:
                east_degrees = 180.

        if south_degrees < -90.:
            func = self.publog.info if south_degrees > -90.001 else self.publog.warning
            func(f"forcing min lat {south_degrees} into range (-90)")
            south_degrees = -90.

        if north_degrees > 90.:
            func = self.publog.info if north_degrees < 90.001 else self.publog.warning
            func(f"forcing max lat {north_degrees} into range (90)")
            north_degrees = 90.

        coordinates = [
            [
                [west_degrees, south_degrees],
                [east_degrees, south_degrees],
                [east_degrees, north_degrees],
                [west_degrees, north_degrees],
                [west_degrees, south_degrees],
            ]
        ]

        bbox = [west_degrees, south_degrees, east_degrees, north_degrees]
        return coordinates, bbox

    def handle_temporal(self) -> tuple:
        """
        Apply temporal default if not found
        """
        dt_start = self.geo.get("datetime_start", None)
        dt_end   = self.geo.get("datetime_end", None)
        if dt_start and dt_end:
            start_datetime = "{}Z".format(dt_start.isoformat())
            end_datetime   = "{}Z".format(dt_end.isoformat())
        else:
            start_datetime = "1850-01-01T00:00:00Z"
            end_datetime = "1850-01-01T00:00:01Z"
        return start_datetime, end_datetime

    def get_file_properties(self, file) -> dict:
        """
        Obtain file title as asset, any file_properties from esgvoc.
        """
    
        properties = {}

        ev_project = ev.projects.get_project(self.project)

        for f in ev_project.catalog_specs.file_properties:
            flabel = f.source_collection
            properties[f'{self.project}:{flabel}'] = self.ncattrs[file].get(flabel,None)

        return file.split('/')[-1], properties

    def get_additional_links(self):
        """
        Derive additional link properties if there are any that can be filled
        """

        # Self provided link info:
        # {"<TITLE>":{
        #    "href":"<URL>",
        #    "type":"<TYPE>" # Optional
        #}}

        add_links = []
        ev_project = ev.projects.get_project(self.project)
        for l in ev_project.catalog_specs.link_properties:
            if l.title in self.link_info:
                link = {
                    'rel':l.rel,
                    'href':self.link_info[l.title]['href'],
                    'title':l.title,
                    'type':self.link_info[l.title].get('type') or l.link_type or 'application/json'
                }
                add_links.append(link)
            elif l.is_required:
                self.publog.error(
                    f'Could not source link info for {l.title} - '
                    'please provide additional link info.'
                )
        return add_links

    def match_title(self, id):
        """
        Match the title by regex to expected esgvoc value from the ID
        """

        pattern = ev.get_project(self.project).catalog_specs.catalog_properties.regex_title[:-1]

        match = re.match(pattern, id)
        if match:
            return match.group(0)
        else:
            raise ValueError(
                f"ID {id} does not conform to pattern {pattern}"
            )

    def get_version_from_id(self, id: str, title: str):
        return id.replace(title,'').split('v')[-1]

    def get_stac_record(self) -> dict:
        """
        Obtain the complete STAC item record."""

        self.publog.info('Extracting NetCDF attributes...')
        self.ncattrs = {}
        for file in self.mapfileinfo:
            f = file['file']
            with Dataset(f) as ds:
                self.ncattrs[f] = ds.attrs

        example_file = self.mapfileinfo[0]['file']
        evm = ESGVocabMapper(
            self.project, 
            self.ncattrs[example_file], 
            example_file,
            log_kwargs={
                'verbose': self.config.get('verbose'),
                'silent': self.config.get('silent')
            },
            overrides=self.overrides,
            exclusions=self.exclusions,
            json_map=self.json_map)

        dataset_id = evm.get_dataset_id()
        properties = evm.get_stac_properties()

        dir_struct = evm.get_directory_structure()

        dataset_title = self.match_title(dataset_id)

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        assets = {}
        for mapf in self.mapfileinfo:
            title, file_props = self.get_file_properties(mapf['file'])
            assets[title] = {
                "href": self.file_to_remote(mapf['file']),
                "description": self.access['description'],
                "type": self.access['type'],
                "roles": ["data"],
                "alternate:name": self.data_node,
                "file:size": mapf['size'],
                "file:checksum": f"1220{mapf['checksum']}",
                "created": now,
                "updated": now,
                "protocol": self.access['protocol'],
                "file:local_path": self.file_to_local(mapf['file'], dir_struct),
                **file_props
            }

            self.geo_info_for_file(mapf['file'])

        coordinates, bbox = self.handle_spatial()
        start_datetime, end_datetime = self.handle_temporal()

        version = self.get_version_from_id(dataset_id, dataset_title)

        all_properties = {
            'title':dataset_title,
            'datetime':None,
            'created':now,
            'updated':now,
            'start_datetime':start_datetime,
            'end_datetime':end_datetime,
            'size': sum([mf['size'] for mf in self.mapfileinfo]),
            'retracted':False,
            'access':self.access['access'],
            'latest':True,
            'version':version,
            'project':self.collection,
            'base_id':dataset_title,
            **properties
        }

        sc_version = ev.get_project(self.project).version
        if not check_url(f'https://esgf.github.io/stac-transaction-api/{self.project}/v{sc_version}/schema.json'):
            self.publog.error(f'Schema for {self.project} {sc_version} not reachable')

        return {
            "type": "Feature",
            "stac_version": "1.1.0",
            "stac_extensions": [
                f"https://esgf.github.io/stac-transaction-api/{self.project}/v{sc_version}/schema.json",
                "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json",
                "https://stac-extensions.github.io/file/v2.1.0/schema.json",
            ],
            "id": dataset_id,
            "geometry": {
                "type": "Polygon",
                "coordinates": coordinates
            },
            "bbox": bbox,
            "collection": self.collection,
            "links": [
                {
                    "rel": "self",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{self.collection}/items/{dataset_id}",
                },
                {
                    "rel": "parent",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{self.collection}",
                },
                {
                    "rel": "collection",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{self.collection}",
                },
                {
                    "rel": "root",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections",
                },
            ] + self.get_additional_links(),
            "properties": all_properties,
            "assets":assets
        }

    def publish_stac_record(self):

        rec = self.get_stac_record()

        if self.save_stac:
            with open(f"local/{rec['id']}.json",'w') as f:
                f.write(json.dumps(rec))
            self.publog.info(f"Saved STAC item to local/{rec['id']}.json")

        if not self.dry_run:

            tc = EGITransactionClient({
                'stac_config':self.config['stac_config'],
                'verbose': self.config.get('verbose'),
                'silent':  self.config.get('silent'),
                'dryrun': None,
                'save-stac': None
            })
            success = tc.publish(rec, publisher_label='esgvoc_publisher')
            if success:
                self.publog.info(f"Successful publication - {rec['id']}")
            else:
                self.publog.info('Publication unsuccessful')

if __name__ == '__main__':

    #mapfile = 'local/cmip7_example.map'
    mapfile = '/home/users/dwest77/cedadev/FUTURA/esg-publisher/mapfiles/obs4MIPs.CNES.AVISO-1-0.mon.zos.gn.20180305.v20180305.map'
    config = '/home/users/dwest77/cedadev/FUTURA/CV_testing/esg-publisher/esg.yaml'
    jsonext = '/home/users/dwest77/cedadev/FUTURA/CV_testing/esg-publisher/local/configs/HadISSTv1.1.json'

    import json
    ea = ESGNetcdfAssembler(
        'obs4MIPs',
        mapfile,
        config
    )

    ea.publish_stac_record()
    # rec = ea.get_stac_record()
    # with open(f"local/{rec['id']}.json",'w') as f:
    #     f.write(json.dumps(rec))

    # ea = ESGNetcdfAssembler('/home/users/dwest77/cedadev/FUTURA/esg-publisher/mapfiles/obs4MIPs.CNES.AVISO-1-0.mon.zos.gn.20180305.v20180305.map')

    # rec = ea.get_stac_record()
    # with open(f"local/{rec['id']}.json",'w') as f:
    #     f.write(json.dumps(rec))

    # file = '/badc/cmip7/data/MIP-DRS7/CMIP7/ScenarioMIP/UKNCSP/UKESM1-3-LL/scen7-vl/r3i1p1f1/glb/mon/zos/tavg-u-hxy-sea/g126/v20261020/zos_tavg-u-hxy-sea_mon_glb_g126_UKESM1-3-LL_scen7-vl_r3i1p1f1_205001-210012.nc'

    # with Dataset(file,'r') as ds:
    #     ncattrs = ds.attrs

    # evm = ESGVocabMapper('cmip7',ncattrs, file, log_kwargs={'silent':False,'verbose':False})
    # #evm.display_mappings()
    # print(evm.get_dataset_id())
    # props = evm.get_stac_properties()

    # # live_props = requests.get('https://search.east.esgf.io/collections/CMIP7/items/MIP-DRS7.CMIP7.ScenarioMIP.UKNCSP.UKESM1-3-LL.scen7-vl.r3i1p1f1.glb.mon.zos.tavg-u-hxy-sea.g126.v20261020').json()['properties']

    # # for p in live_props.keys():
    # #     if not p.startswith('cmip7:'):
    # #         continue

    # #     if live_props[p] != props[p]:
    # #         print(f'Different values for {p} - {live_props[p]} <- {props[p]}')
            

            