import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, Slider

# Function to plot heatmap for the given data
def plot_heatmap(data, title, ax):
    heatmap_data = np.mean(data, axis=2)
    cax = ax.imshow(heatmap_data, cmap='coolwarm', interpolation='nearest')
    ax.set_title(title)
    return cax

# Function to update the heatmap for each frame in the animation
def update_heatmap(frame, data, ax):
    ax.clear()
    cax = plot_heatmap(data[frame], f'Time Point {frame}', ax)
    return cax

# Example data generation
num_time_points = 10
num_blocks_y = 10
num_blocks_x = 10
data = np.random.rand(num_time_points, num_blocks_y, num_blocks_x, 3)

# Create a figure and axis for plotting
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)  # Adjust the layout to fit buttons and slider

# Plot the first frame to initialize the heatmap and colorbar
cax = plot_heatmap(data[0], 'Time Point 0', ax)
colorbar = plt.colorbar(cax)

# Animation setup
ani = animation.FuncAnimation(fig, update_heatmap, frames=num_time_points, fargs=(data, ax), interval=500, repeat=True)

# Play/Pause Button Functions
is_paused = False

def play_pause(event):
    global is_paused
    if is_paused:
        ani.event_source.start()
    else:
        ani.event_source.stop()
    is_paused = not is_paused

# Slider Update Function
def update_frame(val):
    frame = int(slider.val)
    update_heatmap(frame, data, ax)
    fig.canvas.draw_idle()

# Adding Play/Pause Button
ax_play_pause = plt.axes([0.8, 0.05, 0.1, 0.075])  # x, y, width, height
btn_play_pause = Button(ax_play_pause, 'Play')
btn_play_pause.on_clicked(play_pause)

# Adding a Slider
ax_slider = plt.axes([0.2, 0.05, 0.5, 0.03], facecolor='lightgoldenrodyellow')
slider = Slider(ax_slider, 'Frame', 0, num_time_points-1, valinit=0, valstep=1)
slider.on_changed(update_frame)

# Display the plot
plt.show()
