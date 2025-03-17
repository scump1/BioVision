
from dataclasses import dataclass

@dataclass
class DataMixingTime:
    
    tile_size: int = None
    rows: int = None
    columns: int = None
    
    def __init__(self):

        self.global_mixing_data = {}
        self.local_mixing_time_data = {}
    
    def add_global_results(self, image_index: int, entropy: float, variance: float) -> None:
        
        if image_index not in self.global_mixing_data:
            self.global_mixing_data[image_index] = {}
            
        self.global_mixing_data["entropy"][image_index] = entropy
        self.global_mixing_data["variance"][image_index] = variance
    
    # For the local mixing time
    def add_tile(self, image_index: int, value: any):
        """
        Stores a tile data at the specified position
        
        Arguments:
            image_index (int): the image number
            value (dict): contains a tile index (i,j) = [entropy, variance]
        """
        if image_index not in self.local_mixing_time_data:
            self.local_mixing_time_data[image_index] = {}
            
        self.local_mixing_time_data[image_index] = value
        
    def get_tile(self, image_index: int, row: int, col: int):
        """
        Retrieves a tiles data from the specified position
        
        Arguments:
            image_index (int): the xth image in the series
            row, col (int, int): the position of the tile in the grid dimensions n,m
            
        Returns:
            data :)
        """
        return self.local_mixing_time_data.get(image_index, {}).get((row, col), None)

    def add_local_metadata(self, tile_size: int, rows: int, columns: int):

        self.tile_size = tile_size
        self.rows = rows
        self.columns = columns
   