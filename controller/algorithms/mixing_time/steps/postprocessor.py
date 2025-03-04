
import matplotlib.pyplot as plt
import numpy as np

class Postprocessor:
    
    def __init__(self, visualization: bool = False):
        
        self.vis = visualization
    
    # the tile informations are embedded into the dataclass
    def postprocess(self, global_variance: list, global_entropy: list, local_mixtime_dataclass):
        
        # Step 1: the global mixing times. Each step in the list is one frame!
        self.global_mixing_time_calc(global_variance, global_entropy)
        
        # Step 2: the local mixing time. for each frame, plot the current as heatmap in comparison to the final values.
    
    def plot_global_mixing_time(self, data):
    
        """Plot normalized entropy, variance, and their average over image indices."""
        image_indices = sorted(data.global_mixing_data.keys())
        entropies = np.array([data.global_mixing_data[idx]["entropy"] for idx in image_indices])
        variances = np.array([data.global_mixing_data[idx]["variance"] for idx in image_indices])

        # Normalize to [0, 1]
        entropy_normalized = (entropies - entropies.min()) / (entropies.max() - entropies.min() + 1e-9)  # Add small epsilon to avoid division by zero
        variance_normalized = (variances - variances.min()) / (variances.max() - variances.min() + 1e-9)
        
        # Calculate average of normalized values
        averages = (entropy_normalized + variance_normalized) / 2

        plt.figure(figsize=(12, 8))

        # Plot Normalized Entropy
        plt.subplot(3, 1, 1)
        plt.plot(image_indices, entropy_normalized, label="Normalized Entropy", color="blue")
        plt.xlabel("Image Index")
        plt.ylabel("Normalized Entropy")
        plt.title("Global Normalized Entropy Over Time")
        plt.grid(True)
        plt.legend()

        # Plot Normalized Variance
        plt.subplot(3, 1, 2)
        plt.plot(image_indices, variance_normalized, label="Normalized Variance", color="red")
        plt.xlabel("Image Index")
        plt.ylabel("Normalized Variance")
        plt.title("Global Normalized Variance Over Time")
        plt.grid(True)
        plt.legend()

        # Plot Average of Normalized Entropy and Variance
        plt.subplot(3, 1, 3)
        plt.plot(image_indices, averages, label="Average (Entropy + Variance)", color="green")
        plt.xlabel("Image Index")
        plt.ylabel("Average Normalized Value")
        plt.title("Average of Normalized Entropy and Variance Over Time")
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.show()
