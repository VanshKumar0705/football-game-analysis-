from utils import read_video, save_video
from trackers import Tracker
import cv2
from camera_movement_estimator import CameraMovementEstimator
from team_assigner import teamAssigner
from player_ball_assigner import PlayerBallAssigner
import numpy as np
from view_transformer import ViewTransformer
from speed_and_distance_estimator import SpeedAndDistance_Estimator


def main():
   

    video_frames = read_video('input_video/08fd33_4.mp4')

    tracker= Tracker('models/best.pt')

    tracks = tracker.get_object_tracks(video_frames,
                                       read_from_stub=True,
                                       stub_path='stubs/track_stubs.pkl')
    
     # Get object positions 
    tracker.add_position_to_tracks(tracks)
    
    # camera movement estimator
    camera_movement_estimator = CameraMovementEstimator(video_frames[0])
    camera_movement_per_frame = camera_movement_estimator.get_camera_movement(video_frames,
                                                                                read_from_stub=True,
                                                                                stub_path='stubs/camera_movement_stub.pkl')
    camera_movement_estimator.add_adjust_positions_to_tracks(tracks,camera_movement_per_frame)

    #view Transformer
    view_transformer=ViewTransformer()
    view_transformer.add_transformed_position_to_tracks(tracks)
    

    tracks["ball"]=tracker.interpolate_ball_positions(tracks["ball"])

    #Speed and Distance Estimator
    speed_and_distance_estimator=SpeedAndDistance_Estimator()
    speed_and_distance_estimator.add_speed_and_distance_to_tracks(tracks)
    
    #Assign player Team

    team_assigner= teamAssigner()
    team_assigner.assign_team_color(video_frames[0], tracks['players'][0])

    for frame_num, player_track in enumerate(tracks['players']):
        for player_id,track in player_track.items():
            team= team_assigner.get_player_team(video_frames[frame_num],
                                                track['bbox'],
                                                player_id)
            tracks['players'][frame_num][player_id]['team']=team
            tracks['players'][frame_num][player_id]['team_color']=team_assigner.team_colors[team]


    

    # # Assign Ball Aquisition
    player_assigner =PlayerBallAssigner()
    
    team_ball_control= []
   
    for frame_num, player_track in enumerate(tracks['players']):
        ball_bbox = tracks['ball'][frame_num][1]['bbox']
        assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)

        if (assigned_player != -1):
            tracks['players'][frame_num][assigned_player]['has_ball'] = True
            team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
        else:
           if team_ball_control:
            # If the list is not empty, append the last value
            team_ball_control.append(team_ball_control[-1])
           else:
            # If the list is empty (i.e., first frame or no ball assigned), append a default value
            team_ball_control.append(ball_bbox)
       
    team_ball_control= np.array(team_ball_control)
       




    #save cropped image

    for track_id, player in tracks['players'][0].items():
        bbox=player['bbox']
        frame=video_frames[0]

        cropped_image = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]
        cv2.imwrite(f'output_videos/cropped_image.jpg', cropped_image)

        break
    
    output_video_frames= tracker.draw_annotations(video_frames, tracks,team_ball_control)

    ## Draw Camera movement
    output_video_frames = camera_movement_estimator.draw_camera_movement(output_video_frames,camera_movement_per_frame)

    #Draw Speed and distance estimator
    speed_and_distance_estimator.draw_speed_and_distance(output_video_frames,tracks)

    save_video(output_video_frames, 'output_videos/output_video.avi')

if __name__ == '__main__':
    main()

       