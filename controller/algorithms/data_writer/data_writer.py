
from model.utils.SQL.sql_manager import SQLManager

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.logger.global_logger import Logger

class DataWriter:
    """The corresponding data writer functions for each executable algorithm in the AlgorithmManger."""

    def __init__(self):

        self.sql = SQLManager()
        self.logger = Logger("Controller").logger
        
        self.data = InMemoryData()

    def bubble_size_writer(self, results: dict) -> None:
        """Writes the data for the results of a bubble size analysis.
        
        
        Args:
            results = {
                "Image": name,
                "Data": data,
                'Metadata': metadata
            }
                where data is list = [ [cx, cy, diameter, area, surface_area, volume, sur_vol, x_sauter, circularity], ... ]
            
        Return:
            None
        """
        try:            
            result_db = self.data.get_data(self.data.Keys.CURRENT_SLOT_RESULT_DB, namespace=self.data.Namespaces.MEASUREMENT)

            keys = ["CenterX", "CenterY", "EquivalentDiameter", "Area", "SurfaceArea", "Volume", "SpecificSurfaceVolume", "SauterDiameter", "Circularity"]
            data_dict = {}

            data_dict["Image"] = results["Image"]
        
            for ellipse in results["Data"]:
                
                if not ellipse:
                    for i, key in enumerate(keys):
                        data_dict[key] = "Faulty Data"
                else:
                    for i, key in enumerate(keys):
                        data_dict[key] = ellipse[i]

                table, insert = self.sql.generate_sql_statements("BubbleSizeResults", data_dict)

                self.sql.read_or_write(result_db, table, "write")
                self.sql.read_or_write(result_db, insert, "write")
                
        except Exception as e:
            self.logger.warning(f"Error - Could not write bubble sizer results: {e}.")

    def mixing_time_writer(self, data):
        """The data dict gets written to sql.
        
        Args:
            data = {
                "Image": name,
                "Metadata": cmetadata,
                "Data": calibdata
            }
        """
        
        result_db = self.data.get_data("CurrentResultDB", namespace="Measurement")

        data_dict = {}

        # What image and what time
        data_dict["Image"] = data["Image"]
        data_dict["Time"] = data["Timestamp"]

        metadata_keys = ["XBlocka", "YBlocks", "BlockSize", "Orientation"]
        resultskeys = ["Red", "Green", "Blue"]

        metadata = data["Metadata"]
        resultsdata = data["Data"]

        # resultsdata is a dictionary from calibdata 
        # self.changes[key] = {
        #        'red': change_red,
        #        'green': change_green,
        #        'blue': change_blue
        #        }
        # der key entspricht der blocknummer!

        try:
            for i, element in enumerate(metadata):
                data_dict[metadata_keys[i]] = element

            for key in resultsdata.keys():
                for reskey in resultskeys:
                    data_dict["Block" + str(key+1) + str(reskey)] = str(resultsdata[key][reskey])

            table, insert = self.sql.generate_sql_statements("MixingTimeResults", data_dict)

            self.sql.read_or_write(result_db, table, "write")
            self.sql.read_or_write(result_db, insert, "write")

        except Exception as e:
            self.logger.warning(f"Error - Could not write data: {e}.")
            
    def arduino_data_writer(self, data: list) -> None:
        """Takes in data from the arduino and writes to the current result measurement folder.

        Args:
            data (list): [temp, target, fanspeed]
        """
        try:
            
            result_db = self.data.get_data(self.data.Keys.CURRENT_SLOT_RESULT_DB, namespace=self.data.Namespaces.MEASUREMENT)
            
            fanspeed = (float(data[2])/255) * 100
            
            write_data = {
                "CurrentTemperature": float(data[0]),
                "TargetTemperature": float(data[1]),
                "Fanspeed": fanspeed
            }
                        
            table, insert = self.sql.generate_sql_statements("EnvironmentData", write_data)
            
            self.sql.read_or_write(result_db, table, "write")
            self.sql.read_or_write(result_db, insert, "write")
        
        except Exception as e:
            self.logger.warning(f"Could not write Arduino data: {e}.")
            
    def mfc_data_writer(self, read: float) -> None:
        """Writes the massflow to the current ResultDB.

        Args:
            read (list) : [massflow, unit]
        """
        
        try:
            
            result_db = self.data.get_data(self.data.Keys.CURRENT_SLOT_RESULT_DB, namespace=self.data.Namespaces.MEASUREMENT)
            
            write_data = {
                "Massflow": read[0]
            }
            
            table, insert = self.sql.generate_sql_statements("EnvironmentData", write_data)
            
            self.sql.read_or_write(result_db, table, "write")
            self.sql.read_or_write(result_db, insert, "write")
        
        except Exception as e:
            self.logger.warning(f"Error - Could not write MFC data: {e}.")