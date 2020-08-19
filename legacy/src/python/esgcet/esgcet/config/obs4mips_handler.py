"""-*- Python -*-
obs4MIPs project handler
"""
from esgcet.exceptions import *
from esgcet.config import IPCC5Handler
from esgcet.messaging import warning

standard_project_id = 'obs4mips'

class Obs4mipsHandler(IPCC5Handler):

    def validateFile(self, fileobj):
        """Raise ESGInvalidMetadataFormat if the file cannot be processed by this handler."""
        if not fileobj.hasAttribute('project_id'):
            result = False
            message = "No global attribute: project_id"
        else:
            project_id = fileobj.getAttribute('project_id', None).lower()
            result =  (project_id==standard_project_id)
            message = "project_id = %s, should be %s"%(project_id, standard_project_id)
        if not result:
            raise ESGInvalidMetadataFormat(message)

    def getContext(self, **context):
        """
        Read all metadata fields from the file associated with the handler. Typically this is the first file
        encountered in processing. The assumption is that all files contain the global metadata
        to be associated with the project. The file path is in self.path, and may be changed if necessary.

        Calls ``readContext`` to read the file.

        Returns a context dictionary of fields discovered in the file.

        context
          Dictionary of initial field values, keyed on field names. If a field is initialized, it is not overwritten.
        """
        IPCC5Handler.getContext(self, **context)
        return self.context

    def readContext(self, fileInstance, **kw):
        """Get a dictionary of attribute/value pairs from an open file.

        Returns a dictionary of attribute/value pairs, which are added to the handler context.

        fileInstance
          Format handler instance representing the opened file, an instance of FormatHandler
          or a subclass.

        kw
          Optional keyword arguments.

        """
        result = {}
        f = fileInstance.file

        result = IPCC5Handler.readContext(self, fileInstance, **kw)
        if 'project' not in result:
            result['project'] = self.name

        # Parse CMOR table.
        if hasattr(f, 'table_id'):
            tableId = getattr(f, 'table_id')
            fields = tableId.split()

            # Assume table ID has the form 'Table table_id ...'
            if len(fields)>1:
                table = fields[1]
                result['cmor_table'] = table
            else:
                result['cmor_table'] = 'noTable'

        # Read categories as file attributes, for values not already set
        for category in self.getFieldNames():
            if category not in result and hasattr(f, category):
                result[category] = getattr(f, category)

            # Check if mandatory fields are set
            if self.isMandatory(category) and category not in result:
                warning("Mandatory category %s not set for file %s, use -p option?"%(category, fileInstance.path))

        # Check validity
        self.validateContext(result)

        # Return the attribute/value dictionary
        return result
