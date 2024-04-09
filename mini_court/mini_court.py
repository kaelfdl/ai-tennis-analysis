import cv2
import sys
import numpy as np
sys.path.append('../')
import constants
from utils import convert_meters_to_pixel_distance, convert_pixel_distance_to_meters

class MiniCourt():
    def __init__(self, frame):
        self.drawing_rectangle_width = 250
        self.drawing_rectangle_height = 500
        self.buffer = 50
        self.padding_court = 20
        
        self.set_canvas_background_box_position(frame)
        self.set_mini_court_position()
        self.set_court_drawing_kps()
        self.set_court_lines()

    def convert_meters_to_pixels(self, meters):
        return convert_meters_to_pixel_distance(meters, constants.DOUBLE_LINE_WIDTH, self.court_drawing_width)

    def set_court_drawing_kps(self):
        drawing_kps = [0]*28

        # point 0
        drawing_kps[0], drawing_kps[1] = int(self.court_start_x), int(self.court_start_y)
        # point 1
        drawing_kps[2], drawing_kps[3] = int(self.court_end_x), int(self.court_start_y)
        # point 2
        drawing_kps[4] = int(self.court_start_x)
        drawing_kps[5] = self.court_start_y + self.convert_meters_to_pixels(constants.HALF_COURT_LINE_HEIGHT * 2)
        # point 3
        drawing_kps[6] = drawing_kps[0] + self.court_drawing_width
        drawing_kps[7] = drawing_kps[5]
        # #point 4
        drawing_kps[8] = drawing_kps[0] +  self.convert_meters_to_pixels(constants.DOUBLE_ALLEY_DIFFERENCE)
        drawing_kps[9] = drawing_kps[1] 
        # #point 5
        drawing_kps[10] = drawing_kps[4] + self.convert_meters_to_pixels(constants.DOUBLE_ALLEY_DIFFERENCE)
        drawing_kps[11] = drawing_kps[5] 
        # #point 6
        drawing_kps[12] = drawing_kps[2] - self.convert_meters_to_pixels(constants.DOUBLE_ALLEY_DIFFERENCE)
        drawing_kps[13] = drawing_kps[3] 
        # #point 7
        drawing_kps[14] = drawing_kps[6] - self.convert_meters_to_pixels(constants.DOUBLE_ALLEY_DIFFERENCE)
        drawing_kps[15] = drawing_kps[7] 
        # #point 8
        drawing_kps[16] = drawing_kps[8] 
        drawing_kps[17] = drawing_kps[9] + self.convert_meters_to_pixels(constants.NO_MANS_LAND_HEIGHT)
        # # #point 9
        drawing_kps[18] = drawing_kps[16] + self.convert_meters_to_pixels(constants.SINGLES_LINE_WIDTH)
        drawing_kps[19] = drawing_kps[17] 
        # #point 10
        drawing_kps[20] = drawing_kps[10] 
        drawing_kps[21] = drawing_kps[11] - self.convert_meters_to_pixels(constants.NO_MANS_LAND_HEIGHT)
        # # #point 11
        drawing_kps[22] = drawing_kps[20] +  self.convert_meters_to_pixels(constants.SINGLES_LINE_WIDTH)
        drawing_kps[23] = drawing_kps[21] 
        # # #point 12
        drawing_kps[24] = int((drawing_kps[16] + drawing_kps[18])/2)
        drawing_kps[25] = drawing_kps[17] 
        # # #point 13
        drawing_kps[26] = int((drawing_kps[20] + drawing_kps[22])/2)
        drawing_kps[27] = drawing_kps[21]
        
        self.drawing_kps = drawing_kps

    def set_court_lines(self):
        self.lines = [
             (0, 2),
            (4, 5),
            (6,7),
            (1,3),
            
            (0,1),
            (8,9),
            (10,11),
            (10,11),
            (2,3),
            (12, 13)

        ]



    def set_mini_court_position(self):
        self.court_start_x = self.start_x + self.padding_court
        self.court_start_y = self.start_y + self.padding_court
        self.court_end_x = self.end_x - self.padding_court
        self.court_end_y = self.end_y - self.padding_court

        self.court_drawing_width = self.court_end_x - self.court_start_x

    def set_canvas_background_box_position(self, frame):
        frame = frame.copy()

        self.end_x = frame.shape[1] - self.buffer
        self.end_y = self.buffer + self.drawing_rectangle_height
        self.start_x = self.end_x - self.drawing_rectangle_width
        self.start_y = self.end_y - self.drawing_rectangle_height

    def draw_background_rectangle(self, frame):
        shapes = np.zeros_like(frame, np.uint8)
        # Draw the rectangle
        cv2.rectangle(shapes, (self.start_x, self.start_y), (self.end_x, self.end_y), (255, 255, 255), cv2.FILLED)
        out = frame.copy()
        alpha = 0.5
        mask = shapes.astype(bool)
        out[mask] = cv2.addWeighted(frame, alpha, shapes, 1 - alpha, 0 )[mask]
        return out
    
    def draw_court(self, frame):
        for i in range(0, len(self.drawing_kps), 2):
            x = int(self.drawing_kps[i])
            y = int(self.drawing_kps[i+1])
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
        
        # Draw lines
        for line in self.lines:
            start_point = (int(self.drawing_kps[line[0]*2]), int(self.drawing_kps[line[0]*2+1]))
            end_point = (int(self.drawing_kps[line[1]*2]), int(self.drawing_kps[line[1]*2+1]))
            cv2.line(frame, start_point, end_point, (0,0,0), 2)

        # Draw net
        net_start_point = (self.drawing_kps[0], int((self.drawing_kps[1] + self.drawing_kps[5]) / 2))
        net_end_point = (self.drawing_kps[2], int((self.drawing_kps[1] + self.drawing_kps[5]) / 2))
        cv2.line(frame, net_start_point, net_end_point, (255,0,0), 2)

        return frame
    
    def draw_mini_court(self, frames):
        output_frames = []
        for frame in frames:
            frame = self.draw_background_rectangle(frame)
            frame = self.draw_court(frame)
            output_frames.append(frame)
        return output_frames

    def get_start_point_of_mini_court(self):
        return (self.court_start_x, self.court_start_y)
    
    def get_width_of_mini_court(self):
        return self.court_drawing_width

    def get_court_drawing_kps(self):
        return self.drawing_kps