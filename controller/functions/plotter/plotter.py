
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolBar)

from matplotlib.figure import Figure

class Plotter:

    def __init__(self) -> None:
        
        self.figure = None
        self.canvas = None
        self.ax = None

    def plot(self, x: list, y: dict, xlabel=None, ylabel=None, title=None, **plot_kwargs) -> QWidget:
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolBar(self.canvas, None)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.clear()  # Clear previous plots

        # Plot the first y-axis
        first_key = list(y.keys())[0]
        self.ax.plot(x, y[first_key], **plot_kwargs)
        y.pop(first_key)  # Remove the first entry after plotting

        # Set axis labels for the primary axis
        if xlabel:
            self.ax.set_xlabel(xlabel)
        if ylabel:
            self.ax.set_ylabel(ylabel)
        
        # Initialize the list to keep track of created secondary axes
        secondary_axes = []

        # Loop through remaining y-axis data and create secondary y-axes
        for i, (key, y_values) in enumerate(y.items()):
            if i == 0:
                ax_y = self.ax.twinx()
            else:
                # Create another y-axis on the right with an offset
                ax_y = self.ax.twinx()
                ax_y.spines['right'].set_position(('outward', 60 * i))  # Offset each additional y-axis
                secondary_axes.append(ax_y)

            ax_y.plot(x, y_values, **plot_kwargs)
            ax_y.set_ylabel(f'{key}')  # Set the label for each secondary y-axis
            ax_y.tick_params(axis='y')

        # Set plot title if provided
        if title:
            self.ax.set_title(title)
        
        self.canvas.draw()

        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        widget.setLayout(layout)
        
        return widget
    
    def plot_histograms(self, hist_red, hist_green, hist_blue) -> QWidget:
        self.ax.clear()  # Clear previous plots
        
        # Plot histograms for each channel
        self.ax.plot(hist_red, color='r', label='Red Channel')
        self.ax.plot(hist_green, color='g', label='Green Channel')
        self.ax.plot(hist_blue, color='b', label='Blue Channel')
        
        self.ax.set_xlabel('Pixel Intensity')
        self.ax.set_ylabel('Frequency')
        self.ax.set_title('Color Channel Histograms')
        self.ax.legend()
        
        self.canvas.draw()

        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        widget.setLayout(layout)
        
        return widget
    
    def plot_mixingtime_heatmap(self):

        pass
    
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("Matplotlib Plotter Example")
    main_window.setGeometry(100, 100, 800, 600)

    # Create a Plotter instance
    plotter = Plotter()
    # Generate the plot widget
    plot_widget = plotter.plot(
        [1, 2, 3], {1: [0.5, 1, 1.5], "Nochmal Mischzeit": [10, 20, 30]}, # Wir konnen mehrere y Achsen haben!
        xlabel='Time',
        ylabel='Mischzeit',
        title='Sample Plot',
        color='r',         # Additional plot customization
        linestyle='-'     # Additional plot customization
    )

    # Set the central widget of the main window to the plot widget
    main_window.setCentralWidget(plot_widget)

    # Show the main window
    main_window.show()

    # Execute the application
    sys.exit(app.exec())