# Author: Muhammad Abdullah Javaid
# Email: abdullahjavaid0307@gmail.com

import sys
import math
import warnings

import numpy as np
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QVBoxLayout, QHeaderView, QTableWidgetItem
from PyQt5.QtGui import QGradient, QPixmap, QPainter, QLinearGradient, QColor

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from GUI import Ui_MainWindow

warnings.filterwarnings("ignore")


def find_closest_point(ref_point, points_list):
    closest_point = None
    for point in points_list:
        distance = math.sqrt((point[0] - ref_point[0]) ** 2 + (point[1] - ref_point[1]) ** 2)
        if distance < 200:
            closest_point = point
    return closest_point


def generate_gradient_string(red_points, green_points, blue_points):
    gradient = QLinearGradient(0, 0, 1, 0)
    for x in range(0, 4096):
        red = calculate_color(x, red_points)
        green = calculate_color(x, green_points)
        blue = calculate_color(x, blue_points)
        gradient.setColorAt(x / 4095.0, QColor(red, green, blue))
    return gradient_string(gradient)


def reduce_gradient_stops(stops, num_stops=10):
    """
    Reduces a list of gradient stops to a smaller number of stops.

    Arguments:
    stops -- list of tuples (pos, color) representing gradient stops
    num_stops -- desired number of stops in the reduced list (default: 10)

    Returns:
    List of tuples (pos, color) representing the reduced gradient stops
    """
    # Ensure that there are at least two stops
    if len(stops) < 2:
        raise ValueError("At least 2 stops are required.")

    # If the number of stops is less than or equal to the desired number, return the original stops
    if len(stops) <= num_stops:
        return stops

    # Otherwise, calculate the positions of the reduced stops
    reduced_positions = [i * (1.0 / (num_stops - 1)) for i in range(num_stops)]

    # Find the closest original stop for each reduced position
    reduced_stops = []
    for pos in reduced_positions:
        # Find the two closest original stops
        prev_stop = stops[0]
        next_stop = stops[-1]
        for stop in stops:
            if stop[0] < pos:
                prev_stop = stop
            elif stop[0] > pos:
                next_stop = stop
                break

        # Interpolate the color between the two closest stops
        prev_pos, prev_color = prev_stop
        next_pos, next_color = next_stop
        t = (pos - prev_pos) / (next_pos - prev_pos)
        interp_color = QtGui.QColor(
            int((1 - t) * prev_color.red() + t * next_color.red()),
            int((1 - t) * prev_color.green() + t * next_color.green()),
            int((1 - t) * prev_color.blue() + t * next_color.blue()),
            int((1 - t) * prev_color.alpha() + t * next_color.alpha())
        )

        reduced_stops.append((pos, interp_color))

    return reduced_stops


def calculate_color(x, points):

    for i in range(0, len(points) - 1):
        if points[i][0] <= x <= points[i + 1][0]:
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1
            return int(m * x + b)
    return 0


def gradient_string(gradient):
    stops = gradient.stops()
    new = [(stop, color) for stop, color in stops]
    stops = reduce_gradient_stops(new, num_stops=10)
    return ", ".join(
        ["stop:{0:.3f} rgba({1},{2},{3},{4})".format(stop, color.red(), color.green(), color.blue(), color.alpha())
         for stop, color in stops])


def get_column_value_count(table_widget, column_index):
    values = set()
    for row in range(table_widget.rowCount()):
        item = table_widget.item(row, column_index)
        if item is not None:
            value = item.text()
            values.add(value)

    return len(values)


def calculate_gradient(red_points, green_points, blue_points, signal_points):

    # Calculate slopes for each color
    red_slopes = [float(p[1] - red_points[i - 1][1]) / float(p[0] - red_points[i - 1][0]) for i, p in
                  enumerate(red_points) if i > 0]
    green_slopes = [float(p[1] - green_points[i - 1][1]) / float(p[0] - green_points[i - 1][0]) for i, p in
                    enumerate(green_points) if i > 0]
    blue_slopes = [float(p[1] - blue_points[i - 1][1]) / float(p[0] - blue_points[i - 1][0]) for i, p in
                   enumerate(blue_points) if i > 0]

    gradient_values = []
    for signal in signal_points:
        # Find the red, green, and blue values at this signal point
        red = 0
        for i in range(len(red_points) - 1):
            if red_points[i][0] <= signal <= red_points[i + 1][0]:
                red = red_slopes[i] * (signal - red_points[i][0]) + red_points[i][1]
                break

        green = 0
        for i in range(len(green_points) - 1):
            if green_points[i][0] <= signal <= green_points[i + 1][0]:
                green = green_slopes[i] * (signal - green_points[i][0]) + green_points[i][1]
                break

        blue = 0
        for i in range(len(blue_points) - 1):
            if blue_points[i][0] <= signal <= blue_points[i + 1][0]:
                blue = blue_slopes[i] * (signal - blue_points[i][0]) + blue_points[i][1]
                break

        # Calculate the gradient value for this signal point
        gradient_value = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        gradient_values.append(gradient_value)

    return gradient_values


class Main:
    def __init__(self):
        self.MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.ui.frame_2.setLayout(layout)
        self.ax = self.figure.add_subplot(111)

        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

        self.ui.pushButton.clicked.connect(lambda: self.change_active_color("Red"))
        self.ui.pushButton_2.clicked.connect(lambda: self.change_active_color("Green"))
        self.ui.pushButton_3.clicked.connect(lambda: self.change_active_color("Blue"))
        self.ui.pushButton_4.clicked.connect(self.reset_plot)
        self.ui.pushButton_5.clicked.connect(self.export_points)
        self.ui.pushButton_6.clicked.connect(self.save_gradient_image)

        self.points = {"Red": [(0, 0), (4095, 255)],
                       "Green": [(0, 0), (4095, 255)],
                       "Blue": [(0, 0), (4095, 255)]}
        self.slopes = {"Red": [], "Green": [], "Blue": []}

        for color in ["Red", "Green", "Blue"]:
            slopes = [0]
            for i in range(len(self.points[color]) - 1):
                x1, y1 = self.points[color][i]
                x2, y2 = self.points[color][i + 1]
                slope = (y2 - y1) / (x2 - x1)
                slopes.append(slope)
            self.slopes[color] = slopes

        self.selected_point = None
        self.dragging = False
        self.current_color = "Red"
        self.update_graph()

        self.ui.tableWidget.cellChanged.connect(self.update_from_table)
        self.table_change_connected = True

        self.update_table()
        self.update_gradient()

        self.ui.pushButton.setStyleSheet("""background-color: rgb(255, 0, 0);""")

    def calculate_slopes(self):
        for color in ["Red", "Green", "Blue"]:
            slopes = [0]
            for i in range(len(self.points[color]) - 1):
                x1, y1 = self.points[color][i]
                x2, y2 = self.points[color][i + 1]
                slope = (y2 - y1) / (x2 - x1)
                slopes.append(slope)
            self.slopes[color] = slopes

    def reset_plot(self):
        self.selected_point = None
        self.dragging = False
        self.current_color = "Red"

        self.points = {"Red": [(0, 0), (4095, 255)],
                       "Green": [(0, 0), (4095, 255)],
                       "Blue": [(0, 0), (4095, 255)]}

        self.slopes = {"Red": [], "Green": [], "Blue": []}

        for color in ["Red", "Green", "Blue"]:
            slopes = [0]
            for i in range(len(self.points[color]) - 1):
                x1, y1 = self.points[color][i]
                x2, y2 = self.points[color][i + 1]
                slope = (y2 - y1) / (x2 - x1)
                slopes.append(slope)
            self.slopes[color] = slopes

        self.update_graph()
        self.update_table()
        self.update_gradient()

    def change_active_color(self, color):
        self.current_color = color
        self.update_graph()
        self.update_table()
        self.update_gradient()

        if color == "Red":
            self.ui.pushButton.setStyleSheet("""background-color: rgb(255, 0, 0);""")
            self.ui.pushButton_2.setStyleSheet("")
            self.ui.pushButton_3.setStyleSheet("")
        elif color == "Green":
            self.ui.pushButton.setStyleSheet("")
            self.ui.pushButton_2.setStyleSheet("""background-color: rgb(0, 128, 0);""")
            self.ui.pushButton_3.setStyleSheet("")
        elif color == "Blue":
            self.ui.pushButton.setStyleSheet("")
            self.ui.pushButton_2.setStyleSheet("")
            self.ui.pushButton_3.setStyleSheet("""background-color: rgb(4, 4, 255);""")

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        x, y = int(event.xdata), int(event.ydata)

        if event.button == 1:  # Left click
            for point in self.points[self.current_color]:
                if abs(x - point[0]) < 50 and abs(y - point[1]) < 50:
                    self.selected_point = point
                    self.dragging = True
                    break

        elif event.button == 3:  # Right click
            for point in self.points[self.current_color]:
                if abs(x - point[0]) < 50 and abs(y - point[1]) < 50:
                    if len(self.points[self.current_color]) > 2:
                        self.points[self.current_color].remove(point)
                        self.calculate_slopes()
                        self.update_graph()
                        self.update_table()
                        self.update_gradient()
                        break
            else:
                if len(self.points[self.current_color]) < 20:
                    # Add the new point in all the color channels
                    self.points["Red"].insert(-1, (x, y))
                    self.points["Green"].insert(-1, (x, y))
                    self.points["Blue"].insert(-1, (x, y))

                    self.points["Red"] = sorted(self.points["Red"], key=lambda p: p[0])
                    self.points["Green"] = sorted(self.points["Green"], key=lambda p: p[0])
                    self.points["Blue"] = sorted(self.points["Blue"], key=lambda p: p[0])

                    self.calculate_slopes()
                    self.update_graph()
                    self.update_table()
                    self.update_gradient()

    def on_release(self, event):
        self.dragging = False
        self.selected_point = None

    def on_motion(self, event):

        if event.xdata:
            x, y = int(event.xdata), int(event.ydata)
            self.ui.label.setText(f"Cursor: ({x}, {y})")

        if event.inaxes != self.ax or self.selected_point is None:
            return

        else:
            x, y = int(event.xdata), int(event.ydata)
            new_x = np.clip(x, 0, 4095)
            new_y = np.clip(y, 0, 255)

            # Getting the closest point
            closest_point = find_closest_point((new_x, new_y), self.points[self.current_color])

            if closest_point:
                old_point = list(self.points[self.current_color][self.points[self.current_color].index(closest_point)])
                old_point[1] = new_y
                self.points[self.current_color][self.points[self.current_color].index(closest_point)] = tuple(old_point)

            self.calculate_slopes()
            self.update_graph()
            self.update_table()
            self.update_gradient()

    def update_graph(self):
        self.ax.clear()
        self.ax.set_xlim(0, 4095)
        self.ax.set_ylim(0, 255)
        for color in ["Red", "Green", "Blue"]:
            x, y = zip(*self.points[color])
            self.ax.plot(x, y, 'o-', color=color, label=color)

        self.canvas.draw()

    def update_table(self):

        # disconnect the signal from the slot
        if self.table_change_connected:
            self.ui.tableWidget.cellChanged.disconnect(self.update_from_table)
            self.table_change_connected = False

        # Initially clear the table
        self.ui.tableWidget.clear()

        # Add the columns
        self.ui.tableWidget.setColumnCount(5)

        # Get the number of columns in the table
        num_columns = self.ui.tableWidget.columnCount()

        # Calculate the column width based on the table width
        column_width = self.ui.tableWidget.width() // num_columns

        # Make the Header to resizable form
        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Set the width of each column to be the same
        for i in range(num_columns):
            self.ui.tableWidget.setColumnWidth(i, column_width)

        # Add the headers
        self.ui.tableWidget.setHorizontalHeaderLabels(["Signal", "Gradient",
                                                       "Red", "Green", "Blue"])

        # Assuming the dictionary containing the points and slopes is named 'points_dict'
        red_points = self.points['Red']
        green_points = self.points['Green']
        blue_points = self.points['Blue']

        signal_points = [i[0] / 4095 for i in red_points]

        # Add the Row counts for all the red, green, blue points
        self.ui.tableWidget.setRowCount(max(len(red_points), len(green_points), len(blue_points)))

        for i in range(len(red_points)):
            item = QTableWidgetItem(f"{red_points[i][0]}")
            self.ui.tableWidget.setItem(i, 0, item)

        for i in range(len(signal_points)):
            item = QTableWidgetItem(f"{signal_points[i]}")
            self.ui.tableWidget.setItem(i, 1, item)

        for i in range(len(red_points)):
            item = QTableWidgetItem(f"{red_points[i][1]}")
            self.ui.tableWidget.setItem(i, 2, item)

        for i in range(len(green_points)):
            item = QTableWidgetItem(f"{green_points[i][1]}")
            self.ui.tableWidget.setItem(i, 3, item)

        for i in range(len(blue_points)):
            item = QTableWidgetItem(f"{blue_points[i][1]}")
            self.ui.tableWidget.setItem(i, 4, item)

        self.ui.tableWidget.cellChanged.connect(self.update_from_table)
        self.table_change_connected = True

    def update_gradient(self):

        redPoints = self.points['Red']
        greenPoints = self.points['Green']
        bluePoints = self.points['Blue']

        gs = generate_gradient_string(redPoints, greenPoints, bluePoints)

        self.ui.label_2.setStyleSheet(
            f"""border-radius:5px;\nborder: 2px solid #ffffff;\nbackground-color: qlineargradient(spread:pad,x1:0, 
            y1:0, x2:1, y2:0, {gs} );""")
        # print(f"""background-color: qlineargradient(spread:pad,x1:0, y1:0, x2:1, y2:0, {gs} );""")

    def save_gradient_image(self):

        # Show the dialog to save the file
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(None, "Save Graph", "", "PNG Files (*.png);;All Files (*)",
                                                   options=options)

        if file_name:

            redPoints = self.points['Red']
            greenPoints = self.points['Green']
            bluePoints = self.points['Blue']

            gradient_string = generate_gradient_string(redPoints, greenPoints, bluePoints)

            print(gradient_string)

            # Create a QLinearGradient object from the gradient string
            gradient = QLinearGradient(0, 0, 1, 0)
            for stop in gradient_string.split(", "):
                position, color = stop.split()
                r, g, b, a = map(int, color[5:-1].split(","))
                gradient.setColorAt(float(position[5:]), QColor(r, g, b, a))

            # # Create a linear gradient from the gradient string
            # gradient = QLinearGradient(0, 0, 1, 0)
            # for stop in gradient_string.split(', '):
            #     position, color = stop.split(' ')[1:]
            #     gradient.setColorAt(float(position), QColor(color))

            gradient.setCoordinateMode(QGradient.ObjectBoundingMode)

            # Create a pixmap and painter to draw the gradient
            pixmap = QPixmap(300, 100)
            painter = QPainter(pixmap)
            painter.setBrush(gradient)
            painter.drawRect(0, 0, 300, 100)

            # Save the pixmap as a PNG image file
            pixmap.save(file_name, "PNG")

            QPainter.end(painter)

    def export_graph(self):

        # Create a new figure for the graph
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        ax.set_xlim(0, 4095)
        ax.set_ylim(0, 255)
        for color in ["Red", "Green", "Blue"]:
            x, y = zip(*self.points[color])
            ax.plot(x, y, 'o-', color=color, label=color)

        canvas.draw()

        # Set the title and legend
        ax.set_title('Piecewise Linear Gradient')
        ax.legend()

        # Show the dialog to save the file
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(None, "Save Graph", "", "PNG Files (*.png);;All Files (*)",
                                                   options=options)

        if file_name:
            # Save the graph as a PNG image
            canvas.print_figure(file_name, dpi=100)

    def update_from_table(self):
        red_points = []
        green_points = []
        blue_points = []

        # Get the values from the table widget
        for i in range(get_column_value_count(self.ui.tableWidget, 0)):
            red_points.append((int(self.ui.tableWidget.item(i, 0).text()),
                               int(self.ui.tableWidget.item(i, 2).text())))

        for i in range(get_column_value_count(self.ui.tableWidget, 0)):
            green_points.append((int(self.ui.tableWidget.item(i, 0).text()),
                                 int(self.ui.tableWidget.item(i, 3).text())))

        for i in range(get_column_value_count(self.ui.tableWidget, 0)):
            blue_points.append((int(self.ui.tableWidget.item(i, 0).text()),
                                int(self.ui.tableWidget.item(i, 4).text())))

        # update the dictionaries
        self.points['Red'] = red_points
        self.points['Green'] = green_points
        self.points['Blue'] = blue_points

        self.calculate_slopes()
        self.update_graph()
        self.update_table()
        self.update_gradient()

    def export_points(self):

        red_points = self.points["Red"]
        green_points = self.points["Green"]
        blue_points = self.points["Blue"]

        # Use QFileDialog to prompt user for save file location and name
        file_path, _ = QFileDialog.getSaveFileName(None, "Save File", "", "Text Files (*.txt)")

        # Open file in write mode
        with open(file_path, 'w') as f:
            # Write red points to file
            f.write(f"ThemeNamedRedPoints = {len(red_points)};\n")
            f.write(f"ThemeNamedRedX = {{{', '.join(str(x) for x, _ in red_points)}}};\n")
            f.write(f"ThemeNamedRedY = {{{', '.join(str(y) for _, y in red_points)}}};\n\n")

            # Write green points to file
            f.write(f"ThemeNamedGreenPoints = {len(green_points)};\n")
            f.write(f"ThemeNamedGreenX = {{{', '.join(str(x) for x, _ in green_points)}}};\n")
            f.write(f"ThemeNamedGreenY = {{{', '.join(str(y) for _, y in green_points)}}};\n\n")

            # Write blue points to file
            f.write(f"ThemeNamedBluePoints = {len(blue_points)};\n")
            f.write(f"ThemeNamedBlueX = {{{', '.join(str(x) for x, _ in blue_points)}}};\n")
            f.write(f"ThemeNamedBlueY = {{{', '.join(str(y) for _, y in blue_points)}}};\n")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    obj = Main()
    obj.MainWindow.show()
    sys.exit(app.exec_())
