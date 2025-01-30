
from ctypes import Array
import random as rng
import cv2
import numpy as np

from scipy.spatial import cKDTree

class ImageProcessor:
    
    def __init__(self, img: cv2.Mat, path, visualizer: bool = False) -> None:
        
        self.img = img

        self.visability = visualizer
        
        if visualizer is True:
            self.visimg = cv2.imread(path, cv2.IMREAD_ANYCOLOR+cv2.IMREAD_ANYDEPTH)

    def img_process(self) -> list:
        
        ### Preparing
        # Contouring
        inner_cont, outer_cont, isolated_bubbles = self.find_contours()
        ### Calculating
        # We directly identify single bubbles
        iresult = self.isolated_fitter(isolated_bubbles)
        
        # This is for processing overlapping bubbles to still retrieve fairly accurate results
        # Moments for identifying centerpoints
        center_points, add_outer = self.moment_calculation(inner_cont)

        rresult = None
        if center_points:
            # We use the centerpoints, the contours and the filled areas to determine fitting ellipses
            rresult = self.circle_fitter_m2(center_points, outer_cont, add_outer)
        
        ### Evaluating
        trusted_results, metadata = self.evaluater(iresult, rresult)

        if self.visability:
            return trusted_results, metadata, self.visimg

        return trusted_results, metadata
        
    def find_contours(self) -> list:
        """Categorizes contours based on hierarchy level: even levels as outer contours and odd levels as inner contours."""

        # Retrieve contours and hierarchy from the image
        tree_contours, hierarchy = cv2.findContours(self.img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        
        # Flatten the hierarchy array for easier indexing
        hierarchy = hierarchy[0]

        # Initialize lists to store inner and outer contours
        inner_contours = []
        outer_contours = []
        
        isolated_bubble_contours = []

        processed_indices = set()

        for i, contour in enumerate(tree_contours):
            if i in processed_indices:
                continue  # Skip already processed contours

            # Check if this is an outer contour (no parent)
            if hierarchy[i][3] == -1:
                # Check if it has exactly one child
                child_idx = hierarchy[i][2]
                if child_idx != -1 and hierarchy[child_idx][0] == -1:
                    # Isolated bubble: Append only the outer contour
                    if len(contour) > 15:
                        isolated_bubble_contours.append(contour)
                        processed_indices.add(child_idx)  # Mark child as processed
                else:
                    # Append to outer contours (overlapping bubbles or others)
                    if len(contour) > 15:
                        outer_contours.append(contour)
            else:
                # Append to inner contours (if size > threshold)
                if len(contour) > 15:
                    inner_contours.append(contour)

        return inner_contours, outer_contours, isolated_bubble_contours

    def isolated_fitter(self, conts: list) -> dict:
        """
        Filters contours to retain only 'bubbly' contours and extracts their properties.

        Args:
            conts (list): List of contours.

        Returns:
            list: List of dictionaries containing properties of filtered contours.
        """
        result = []
        
        for cont in conts:
            
            area = cv2.contourArea(cont)
            perimeter = cv2.arcLength(cont, True)

            if perimeter == 0 or area < 1000:
                continue

            circularity = 4 * np.pi * area / (perimeter**2)
            if circularity < 0.5:
                continue

            ### Here we can just extract the information
            M = cv2.moments(cont)
            
            if M["m00"]:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            
            # real radius
            radius = cv2.pointPolygonTest(cont, (cX, cY), True)
            
            # mathmatical radius comes from the area assuming a perfect circle
            mradius = np.sqrt(4 * area / np.pi)
            radius_deviation = radius / mradius
            
            bubble = [(cX, cY), area, perimeter, mradius, circularity, radius_deviation]
            
            result.append(bubble)
            
            if self.visability:
                cv2.circle(self.visimg, (cX, cY), 5, (255, 0,  0), -1)
                cv2.drawContours(self.visimg, cont, -1, (0,255,0), 3)
            
        return result            

    def moment_calculation(self, inner_conts: list) -> Array | list:
        """Calculates moments for image detection purposes.
        
        Args:
            inner_conts (list): List of inner contours detected by edge detection.
            
        Returns:
            center_points (list): a list of innner contour center points
            add_outer (list): a list of falsly classified inner conts that are actually outer conts
        """      
        center_points = []
        add_outer = []

        for contour in inner_conts:
            
            if len(contour) < 10:
                continue
            
            # We also sort inner contours for unrealistic stuff like white dots, elongated shit and more
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)

            if perimeter == 0 or area < 500:
                continue
            
            M = cv2.moments(contour)

            # We calculate the center point
            if M["m00"]:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                center_points.append((cX, cY))

                # We nned to detect the derivation from the convex hull in %
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                
                deviation = ( (hull_area - M["m00"]) / hull_area ) if hull_area > 0 else np.inf
                
                if deviation > 0.25:
                    add_outer.append(contour)

        return center_points, add_outer
 
    def circle_fitter_m2(self, center_points: list, outer_contours:list , inouter:list , radius:int = 25, accuracy : int = 250) -> list:
        """
        Fit ellipses to contours based on center points.

        Parameters:
        - self: An object that contains img_rgb and visualizer.
        - center_points: List of (x, y) tuples representing center points.
        - outer_contours: List of contours (numpy arrays).
        - radius: Radius for generating circle points around center points.
        - accuracy: Number of points to sample around the circumference of the circle.

        Returns:
        - results: Dictionary containing fitted ellipses.
        """
        results = []

        # Precompute angle-based points
        angles = np.linspace(0, 2 * np.pi, accuracy)
        unit_circle = np.column_stack((np.cos(angles), np.sin(angles)))

        # Convert center_points to numpy array
        center_points = np.array(center_points)
        if center_points.ndim != 2 or center_points.shape[1] != 2:
            raise ValueError("center_points must be of shape (N, 2) where N is the number of center points.")

        # Tree
        for cont in inouter:
            outer_contours.append(cont)
        
        # A tree for all contuor points
        all_contour_points = np.vstack([np.array(ocont).reshape(-1, 2) for ocont in outer_contours])
        tree = cKDTree(all_contour_points)
        
        # Here we actually reconstruct the ellipses
        for centerpoint in center_points:
            # Calculate the shortest distance from the center point to the contour
            cx, cy = centerpoint
            shortest_distance = float('inf')
            for contour in outer_contours:
                distance = abs(cv2.pointPolygonTest(contour, (int(cx), int(cy)), True))
                if distance < shortest_distance:
                    shortest_distance = distance
    
            # The shortest distance as the radius
            adaptive_radius = shortest_distance if shortest_distance > 0 else radius
            
            # Generate points around the centerpoint
            circle_points = centerpoint + adaptive_radius * unit_circle

            # Find nearest neighbors efficiently
            _, indices = tree.query(circle_points)
            rcontour = all_contour_points[indices]

            if len(rcontour) > 5:  # Ensure enough points for fitting
                ellipse = cv2.fitEllipse(rcontour)
                _, (major, minor), _ = ellipse  # Unpacking ellipse parameters
                                
                # Filtering based on ellipse dimensions and aspect ratio
                if major < 5 or minor < 5:
                    continue  # Skip small ellipses

                aspect_ratio = major / minor if minor != 0 else 0
                if aspect_ratio < 0.5 or aspect_ratio > 1.5:  
                    continue  # Skip ellipses that are too elongated

                results.append(ellipse)
        
        # Here we check for closly aligned ellipses as we now have centerpoints and ellipses -> Maybe later
        # center_kd_tree = cKDTree(center_points)

        if self.visability:
            for ellipse in results:
                center, _, _ = ellipse
                cx, cy = center
                cv2.circle(self.visimg, (int(cy), int(cy)), 5, (255, 0, 0), -1)
                cv2.ellipse(self.visimg, ellipse, (0, 0, 255), 3)

        return results

    def evaluater(self, iresult: list, rresult: list = None) -> list:
        """We check each detected bubble again for errors, evaluate how 'good' the results are and then create metadata trustscore.

        Args:
            iresult (list): results from isolated bubbles
            rresult (list): result from recreated overlapping bubbles

        Returns:
            list: two resultlist
        """
        
        trusted_result = {
            "circles" : [],
            "ellipses": []
        }

        metadata = {
            "circles": [],
            "ellipses": []
        }

        if iresult: 
            # First we take the isolated bubbles: All isolated works are trusted, we just split data
            for result in iresult:
                center, area, perimeter, mradius, circularity, radius_deviation = result
                
                trusted_result["circles"].append([center, area, mradius, circularity])
                metadata["circles"].append([perimeter, radius_deviation])
        
        if rresult:
            h, w = self.img.shape
            for result in rresult:
                center, (major, minor), angle = result

                # Calculate semi-major and semi-minor axes
                a = major / 2
                b = minor / 2

                # Area of the ellipse
                area = np.pi * a * b

                # Perimeter (Ramanujan's formula)
                perimeter = np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))

                # Circularity
                circularity = (4 * np.pi * area) / (perimeter ** 2)

                # Create an empty mask for the ellipse
                mask = np.zeros((h, w), dtype=np.uint8)

                # Draw the ellipse onto the mask
                cv2.ellipse(mask, (tuple(map(int, center)), (int(major), int(minor)), angle), 255, thickness=-1)

                # Compute overlap with the white area of the input binary image
                overlap = cv2.bitwise_and(self.img, mask)
                overlap_area = np.sum(overlap == 255)

                overlapscore = area/overlap_area if overlap_area > 0 else np.inf
                metad = [perimeter, overlapscore]
            
                if overlapscore > 0.5:
                    trusted_result["ellipses"].append(result)
                    metadata["ellipses"].append(metad)
            
        
        return trusted_result, metadata

class Visualizer:
          
    def visualize_image(self, img):
        
        resized = cv2.resize(img, (225, 950))
        cv2.imshow("Image", resized)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def visualize_contours(self, contours, img):
        # Draw contours
        drawing = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
        for i in range(len(contours)):
            color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
            cv2.drawContours(drawing, contours, i, color, 2)

        self.visualize_image(drawing)