from abc import ABC, abstractmethod

class ESGPubHandlerBase(ABC):
    def __init__(self, logger):
        self.publog = logger

    @abstractmethod
    def get_scanfile_dict(self, scandata, mapdata):
        """
        Get a dictionary associated with scanned data for the files, indexed by filename
        File-specific metadata, eg the tracking id of the file.  
        """
        pass

    @abstractmethod
    def get_attrs_dict(self, scanobj):
        """
        Return an a dictionary of the global attributes
        """
        pass

    @abstractmethod
    def get_variables(self, scanobj):
        """
        Returns a dictionary of variables, indexed by the names/ids of the variables
        """
        pass

    @abstractmethod
    def get_variable_list(self, variables):
        """
        returns the names/ids of the variables given a "varibales" object
        """
        pass

    @abstractmethod
    def set_bounds(self, record, scanobj):
        """
        Format-specific logic to set the bounds
        record (dict): the dataset record context 
        """
        pass