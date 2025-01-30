
import cv2

class ImageProcessor:

    def __init__(self, img) -> None:

        self.img = img

        self.result = {}

    def process(self, granularity=1) -> dict:

        """This processes a given image with a certain granularity.

        Args:
            granularity (float): Baseline 1. The higher the granularity the higher the resolution, and vice versa. Requierd > 0
        """

        # Step 1: Grid the image
        self.image_grid(granularity)

        # Step 2: Calculate the Histograms over the image
        self.calculate_hists()

        return self.result

    def image_grid(self, granularity):
        """Divides the image into a grid of square blocks based on the granularity factor."""

        # Getting the image dimensions
        height = self.img.shape[0]
        width = self.img.shape[1]

        # Determine the smaller dimension to maintain square blocks
        min_dimension = min(height, width)

        # Calculate the side length of the square blocks based on granularity
        block_size = max(1, int(min_dimension * granularity))

        # Calculate the number of blocks in each direction
        num_blocks_y = int(height / block_size) + (1 if height % block_size != 0 else 0)
        num_blocks_x = int(width / block_size) + (1 if width % block_size != 0 else 0)

        self.result["Metadata"] = [num_blocks_x, num_blocks_y, block_size, 'width' if width < height else 'height']

        # List to hold the grid blocks
        self.grid_blocks = []

        # Loop over the image to create square blocks
        for y in range(num_blocks_y):
            for x in range(num_blocks_x):
                # Calculate the start and end coordinates of the block
                start_y = y * block_size
                end_y = min((y + 1) * block_size, height)
                start_x = x * block_size
                end_x = min((x + 1) * block_size, width)
                
                # Slicing the image to get the square block
                block = self.img[start_y:end_y, start_x:end_x]
                self.grid_blocks.append(block)

    def calculate_hists(self):
        """Calculates histograms for each channel of the image blocks."""

        # Determine the bit depth by checking the image's data type
        if self.img.dtype == 'uint8':
            # 8-bit image
            hist_range = [0, 256]
        elif self.img.dtype == 'uint16':
            # 12-bit image (assuming 12-bit stored in 16-bit containers)
            hist_range = [0, 4096]
        else:
            raise ValueError("Unsupported image bit depth.")

        for i, block in enumerate(self.grid_blocks):
            # Compute histograms for each channel
            hist_red = cv2.calcHist([block], [0], None, [hist_range[-1]], hist_range)
            hist_green = cv2.calcHist([block], [1], None, [hist_range[-1]], hist_range)
            hist_blue = cv2.calcHist([block], [2], None, [hist_range[-1]], hist_range)

            self.result[i] = [hist_red, hist_green, hist_blue]