from utils import (read_video, 
                   save_video,
                   measure_distance,
                   convert_pixel_distance_to_meters,
                   draw_player_stats
                   )

from trackers import PlayerTracker, BallTracker
from court_line_detector import CourtLineDetector
from mini_court import MiniCourt

from copy import deepcopy
import cv2
import pandas as pd
import constants

def main():
    # Read video
    input_video_path = "input_videos/input_video.mp4"
    video_frames = read_video(input_video_path)

    # Detect players and ball
    player_tracker = PlayerTracker(model_path='yolov8x')
    ball_tracker = BallTracker(model_path='models/yolo5_last.pt')
    player_detections = player_tracker.detect_frames(video_frames, 
                                                     read_from_stub=True, 
                                                     stub_path='tracker_stubs/player_detections.pkl')

    ball_detections = ball_tracker.detect_frames(video_frames, 
                                                     read_from_stub=True, 
                                                     stub_path='tracker_stubs/ball_detections.pkl')

    ball_detections = ball_tracker.interpolate_ball_positions(ball_detections)

    # Court line detector model
    court_model_path = 'models/keypoints_model.pth'
    court_line_detector = CourtLineDetector(court_model_path)
    court_kps = court_line_detector.predict(video_frames[0])

    # Choose players
    player_detections = player_tracker.choose_and_filter_players(player_detections, court_kps)

    # Minicourt
    mini_court = MiniCourt(video_frames[0])

    # Detect ball shots
    ball_shot_frames = ball_tracker.get_ball_shot_frames(ball_detections)
    print(ball_shot_frames)

    # Convert positions to mini court positions
    player_mini_court_detections, ball_mini_court_detections = mini_court.convert_bbox_to_mini_court_coordinates(player_detections,
                                                                                                                 ball_detections,
                                                                                                                 court_kps
                                                                                                                 )
    player_stats_data = [
        {
            'frame_num': 0,
            'player_1_number_of_shots': 0,
            'player_1_total_shot_speed': 0,
            'player_1_last_shot_speed': 0,
            'player_1_total_player_speed': 0,
            'player_1_last_player_speed': 0,

            'player_2_number_of_shots': 0,
            'player_2_total_shot_speed': 0,
            'player_2_last_shot_speed': 0,
            'player_2_total_player_speed': 0,
            'player_2_last_player_speed': 0
        }
    ]

    for ball_shot_idx in range(int(len(ball_shot_frames)) - 1):
        start_frame = ball_shot_frames[ball_shot_idx]
        end_frame = ball_shot_frames[ball_shot_idx + 1]
        ball_shot_time_in_seconds = (end_frame - start_frame) / 30

        # Get distance covered by the ball
        distance_covered_by_ball_pixels = measure_distance(ball_mini_court_detections[start_frame][1],
                                                           ball_mini_court_detections[end_frame][1])

        distance_covered_by_ball_meters = convert_pixel_distance_to_meters(distance_covered_by_ball_pixels,
                                                                           constants.DOUBLE_LINE_WIDTH,
                                                                           mini_court.get_width_of_mini_court()
                                                                           )
        
        # Speed of the ball shot in km/h
        speed_of_ball_shot = distance_covered_by_ball_meters / ball_shot_time_in_seconds * 3.6

        # Player who shot the ball
        player_positions = player_mini_court_detections[start_frame]
        player_ball_shot = min(player_positions.keys(), key=lambda x: measure_distance(ball_mini_court_detections[start_frame][1],
                                                                                       player_positions[x]))

        # Opponent player speed
        opponent_player_id = 1 if player_ball_shot == 2 else 2
        distance_covered_by_opponent_pixel = measure_distance(player_mini_court_detections[start_frame][opponent_player_id],
                                                              player_mini_court_detections[end_frame][opponent_player_id])
        distance_covered_by_opponent_meters = convert_pixel_distance_to_meters(distance_covered_by_opponent_pixel,
                                                                               constants.DOUBLE_LINE_WIDTH,
                                                                               mini_court.get_width_of_mini_court())
        speed_of_opponent = distance_covered_by_opponent_meters / ball_shot_time_in_seconds * 3.6

        current_player_stats = deepcopy(player_stats_data[-1])
        current_player_stats['frame_num'] = start_frame
        current_player_stats[f'player_{player_ball_shot}_number_of_shots'] += 1
        current_player_stats[f'player_{player_ball_shot}_total_shot_speed'] += speed_of_ball_shot
        current_player_stats[f'player_{player_ball_shot}_last_shot_speed'] = speed_of_ball_shot
        current_player_stats[f'player_{player_ball_shot}_total_player_speed'] += speed_of_opponent
        current_player_stats[f'player_{player_ball_shot}_last_player_speed'] = speed_of_opponent

        player_stats_data.append(current_player_stats)

    player_stats_data_df = pd.DataFrame(player_stats_data)
    frames_df = pd.DataFrame({'frame_num': list(range(len(video_frames)))})
    player_stats_data_df = pd.merge(frames_df, player_stats_data_df, on='frame_num', how='left')
    player_stats_data_df = player_stats_data_df.ffill()
    player_stats_data_df['player_1_average_shot_speed'] = player_stats_data_df['player_1_total_shot_speed'] / player_stats_data_df['player_1_number_of_shots']
    player_stats_data_df['player_2_average_shot_speed'] = player_stats_data_df['player_2_total_shot_speed'] / player_stats_data_df['player_2_number_of_shots']
    player_stats_data_df['player_1_average_player_speed'] = player_stats_data_df['player_1_total_player_speed'] / player_stats_data_df['player_2_number_of_shots']
    player_stats_data_df['player_2_average_player_speed'] = player_stats_data_df['player_2_total_player_speed'] / player_stats_data_df['player_1_number_of_shots']



    # Draw output

    ## Draw player bounding boxes
    output_video_frames = player_tracker.draw_bboxes(video_frames, player_detections)
    output_video_frames = ball_tracker.draw_bboxes(video_frames, ball_detections)
    

    ## Draw court keypoints
    output_video_frames = court_line_detector.draw_kps_on_video(output_video_frames, court_kps)
    
    ## Draw mini court
    output_video_frames = mini_court.draw_mini_court(output_video_frames)
    output_video_frames = mini_court.draw_points_on_mini_court(output_video_frames, player_mini_court_detections)
    output_video_frames = mini_court.draw_points_on_mini_court(output_video_frames, ball_mini_court_detections, color=(0, 255, 255))

    output_video_frames = draw_player_stats(output_video_frames, player_stats_data_df)

    ## Draw frame number on top left corner
    for i, frame in enumerate(output_video_frames):
        cv2.putText(frame, f"Frame: {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    save_video(output_video_frames, "output_videos/output_video.avi")

if __name__ == "__main__":
    main()