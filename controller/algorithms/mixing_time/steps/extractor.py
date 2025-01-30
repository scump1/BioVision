
import numpy as np


class Extractor:

    def __init__(self, result=None, calibresult=None, calib=False) -> None:
        
        self.results = result
        self.calibresult = calibresult

        self.calib_cycle = calib

    def extract(self):

        # TO different pathways here, we either have the calib img alone or two results
        if self.calib_cycle:

            self.data = {}

            for key in self.calibresult.keys():
                
                change_red = self.calibresult[key][0]
                change_green = self.calibresult[key][1]
                change_blue = self.calibresult[key][2]
                    
                change_red_avg = np.average(change_red)
                change_red_max = np.max(change_red)
                change_red_min = np.min(change_red)
                
                change_green_avg = np.average(change_green)
                change_green_max = np.max(change_green)
                change_green_min = np.min(change_green)
                
                change_blue_avg = np.average(change_blue)
                change_blue_max = np.max(change_blue)
                change_blue_min = np.min(change_blue)


                self.data[key] = {
                    'Red': [change_red_avg, change_red_max, change_red_min],
                    'Green': [change_green_avg, change_green_max, change_green_min],
                    'Blue': [change_blue_avg, change_blue_max, change_blue_min]
                }

            return self.data

        else:

            # Step 1: We determine the change compared to the baseline
            self.change_result = self.calculate_change()

            return self.change_result

    def calculate_change(self):
        
        self.changes = {}

        for key in self.results.keys():

            rred, rgreen, rblue = self.results[key]
            cred, cgreen, cblue = self.calibresult[key]

            # Calculating the change for every channel here
            change_red = self.chi_square_distance(rred, cred)
            change_green = self.chi_square_distance(rgreen, cgreen)
            change_blue = self.chi_square_distance(rblue, cblue)
            
            change_red_avg = np.average(change_red)
            change_red_max = np.max(change_red)
            change_red_min = np.min(change_red)
            
            change_green_avg = np.average(change_green)
            change_green_max = np.max(change_green)
            change_green_min = np.min(change_green)
            
            change_blue_avg = np.average(change_blue)
            change_blue_max = np.max(change_blue)
            change_blue_min = np.min(change_blue)

            self.changes[key] = {
            'Red' : [change_red_avg, change_red_max, change_red_min],
            'Green': [change_green_avg, change_green_max, change_green_min],
            'Blue': [change_blue_avg, change_blue_max, change_blue_min]
            }
        
        return self.changes

    def chi_square_distance(self, hist1, hist2):
        """Computes the Chi Square Distance between two histograms. Small epsilon is applied to prevent division by zero."""
        return 0.5 * np.sum(((hist1 - hist2) ** 2) / (hist1 + hist2 + 1e-10))  # Adding small epsilon to avoid division by zero
