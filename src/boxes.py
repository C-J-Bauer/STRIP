import json
import os
from matplotlib.widgets import Cursor
import math


class Boxes(object):
    def __init__(self, filename, projection_filename, data, do_zoom=False, zoom = [], mirror=False):
        if do_zoom:
            self.x_offset = zoom[1]
            self.y_offset = zoom[0]
        else:
            self.x_offset = 0
            self.y_offset = 0
        self.filename = filename
        self.projection_filename = projection_filename
        self.data = data
        if mirror:
            self.mirror = int(data.shape[0]/2)
        else:
            self.mirror = None
        self.boxes = self.read_boxes_file()    
        self.pending = []
        self.left = []
        self.right = []
        self.prev_pending = None

    
    def read_boxes_file(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, 'r') as f:
            boxes = json.load(f)
        return boxes
    
    def save_boxes(self):
        with open(self.filename, 'w') as f:
            json.dump(self.boxes, f)
    
    def has_boxes(self):
        return len(self.boxes) > 0
    
    def shift_box(self, box):
        return [box[0] - self.y_offset, box[1] - self.x_offset, box[2] - self.y_offset, box[3] - self.x_offset]
    
    def plot_boxes(self, plt):
        if self.prev_pending:
            for line in self.prev_pending:
                line.remove()
            self.prev_pending = None
        if self.pending:
            box = self.shift_box(self.pending)
            # draw a cyan rectangle
            self.prev_pending = plt.plot([box[1], box[1], box[3], box[3], box[1]], [box[0], box[2], box[2], box[0], box[0]], 'c-')
        for unshifted_box in self.boxes:
            box = self.shift_box(unshifted_box)
            # draw a green rectangle
            plt.plot([box[1], box[1], box[3], box[3], box[1]], [box[0], box[2], box[2], box[0], box[0]], 'g-')
    
    
    def left_click(self, plt, x, y):
        x = x+ self.x_offset
        y = y+ self.y_offset
        self.left = [x, y]
        self.make_pending(plt)
        
    def right_click(self, plt, x, y):
        x = x+ self.x_offset
        y = y+ self.y_offset
        self.right = [x, y]
        self.make_pending(plt)
        
    def make_pending(self, plt):
        if self.left and self.right:
            pending = [self.left[1], self.left[0], self.right[1], self.right[0]]
            if self.no_overlap(pending):
                self.pending = pending
        elif not (self.left or self.right):
            self.pending = []
        self.plot_boxes(plt)
        
    def no_overlap(self, box):
        # TODO: check if the box overlaps with any of the existing boxes
        return True
        
    def calc_mirror(self):
        return [2*self.mirror - self.pending[0], self.pending[1], 2*self.mirror - self.pending[2], self.pending[3]]    
        
    def promote_pending(self, plt):
        if self.pending:
            self.boxes.append(self.pending)
            if self.mirror:
                self.boxes.append(self.calc_mirror())
            self.pending = []
            self.right = []
            self.left = []
            self.save_boxes()
            self.calc_and_save_projection()
            self.plot_boxes(plt)  
            
    def point_loop_ranges(self, box):
        y_values = sorted([box[0], box[2]])
        x_values = sorted([box[1], box[3]])
        return y_values, x_values
        
    
    def calc_and_save_projection(self):
        projection = [0.0] * self.data.shape[1]
        for box in self.boxes:
            y_values, x_values = self.point_loop_ranges(box)
            for y in range(y_values[0], y_values[1]):
                for x in range(x_values[0], x_values[1]):
                    projection[x] += self.data[y][x]
        with open(self.projection_filename, 'w') as f:
            json.dump(projection, f)        
            
    def clear_pending(self, plt):
        self.pending = []
        self.right = []
        self.left = []
        self.plot_boxes(plt)      
    
        
        
def set_up_cursors(plt, ax, fig, boxes):
    # Defining the cursor
    cursor = Cursor(ax, horizOn=True, vertOn=True, useblit=True,
                    color = 'r', linewidth = 1)
    # Creating an annotating box
    annot = ax.annotate("", xy=(0,0), xytext=(-40,40),textcoords="offset points",
                        bbox=dict(boxstyle='round4', fc='linen',ec='k',lw=1),
                        arrowprops=dict(arrowstyle='-|>'))
    annot.set_visible(False)
    # Function for storing and showing the clicked values
    def onclick(event):
        x = event.xdata
        y = event.ydata
        
        # check if right buttom clicked
        if event.button == 3:
            # printing the values of the selected point
            x = int(math.ceil(x))
            y = int(math.ceil(y))
            annot.xy = (x,y)
            text = "({}, {})".format(x,y)
            annot.set_text(text)
            annot.set_visible(True)
            boxes.right_click(plt, x, y)
            fig.canvas.draw() #redraw the figure

        elif event.button == 1:
            # printing the values of the selected point
            x = int(x)
            y = int(y)
            annot.xy = (x,y)
            text = "({}, {})".format(x,y)
            annot.set_text(text)
            annot.set_visible(True)
            boxes.left_click(plt, x, y)
            fig.canvas.draw() #redraw the figure
            
    def onkey(event):
        if event.key == '+':
            boxes.promote_pending(plt)
        elif event.key == 'escape':
            boxes.clear_pending(plt)
        annot.set_visible(False)
        
    fig.canvas.mpl_connect('button_press_event', onclick)
    fig.canvas.mpl_connect('key_press_event', onkey)
    plt.show()    
