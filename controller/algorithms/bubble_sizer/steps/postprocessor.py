
import numpy as np

class PostProcessor:

    def __init__(self, result: dict) -> None:
        
        # The given data
        
        self.circles = result["circles"]
        # The circles area already precalculated as form of trusted result
        # trusted_result["circles"].append([center, area, mradius, circularity])
        
        self.ellipses = result["ellipses"]
        # the ellipses area already trusted but need some more calculation to only retrieve circle results
        # trusted_result["ellipses"].append(ellipse)
        
        
        # The return data dict
        # we want standardized results of form : result = [cx, cy, diameter, area, surface_area, volume, sur_vol, x_sauter, circularity]
        self.data = []

    def process(self):

        self.calculations_circles()
        
        self.calculations_ellipses()

        return self.data

    def calculations_circles(self):
        
        for circle in self.circles:
            try:
                center, area, mradius, circularity = circle
                cx, cy = center

                # Calculations
                diameter = 2 * mradius
                surface_area = 4 * np.pi * (mradius ** 2)
                volume = (4 / 3) * np.pi * (mradius ** 3)

                # Safeguard against division by zero
                sur_vol = surface_area / (volume + 1e-8)

                # Sauter diameter
                x_sauter = 6 / sur_vol

                # Append results
                result = [cx, cy, diameter, area, surface_area, volume, sur_vol, x_sauter, circularity]
                self.data.append(result)
            except Exception as e:
                print(f"Error processing circle {circle}: {e}")

    def calculations_ellipses(self):

        # Äquivalenzdurchmesser -> Der Durchmesser den ein Kreis mit gleicher Fläche hätte

        for ellipse in self.ellipses:
            try:
                center, (major, minor), _ = ellipse
                cx, cy = center

                # Projected area and equivalent diameter
                A_proj = np.pi * (major / 2) * (minor / 2)
                radius = np.sqrt(A_proj / np.pi)
                D_eq = radius * 2

                # Sphericity
                sphericity = 0 if major == 0 else minor / major

                # Equivalent sphere properties
                volume = (4 / 3) * np.pi * (radius ** 3)
                surface_area = 4 * np.pi * (radius ** 2)

                # Safeguard against division by zero
                sur_vol = surface_area / (volume + 1e-8)

                # Sauter diameter
                x_sauter = 6 / sur_vol

                # Append results
                result = [cx, cy, D_eq, A_proj, surface_area, volume, sur_vol, x_sauter, sphericity]
                self.data.append(result)
                
            except Exception as e:
                print(f"Error processing ellipse {ellipse}: {e}")