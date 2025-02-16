import matplotlib.pyplot as plt
import numpy as np

def function(x, y, z):
    """
    Input - x, y, z measurements
    Output - 3D plot of the measurements
    """
    # Setup the figure and axis for model
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    # Plot the data
    ax.plot_surface(x, y, z, cmap='viridis')
    ax.set_aspect('equal')

    # Turn off graphy stuff
    ax.axis('off')
    
    # Save the plot to a variable
    model = plt.show()

    # Send model back to the main thread
    return model