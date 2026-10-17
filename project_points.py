
 # Get corresponding 3D points of the Charuco corners
import cv2
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt
import math
PATH_TO_YOUR_IMAGES = './detectedMarkersDrawn'
def projectPoints(charucoIds, charucoCorners, img_name, cameraMatrix, distCoeffs, rvec, tvec, board):
    
    objPoints = board.getChessboardCorners()[charucoIds.flatten()]

    # Project 3D points using the calibration
    imgPoints_proj, _ = cv2.projectPoints(objPoints, rvec, tvec, cameraMatrix, distCoeffs)
    img= cv2.imread(img_name)
    
    cv2.drawFrameAxes(img, cameraMatrix, distCoeffs, rvec, tvec, length=341.4/16, thickness=10)
    # if(img_name[23:]=="0.png"):
    #     print("imgPoints_proj", imgPoints_proj)
    # Draw comparison between detected and projected points
    for detected, projected in zip(charucoCorners, imgPoints_proj):
        x1, y1 = int(detected[0][0]), int(detected[0][1])  # Detected
        x2, y2 = int(projected[0][0]), int(projected[0][1])  # Projected

        # Detected point (green)
        cv2.circle(img, (x1, y1), 5, (0, 255, 0), -1)

        # Projected point (red)
        cv2.circle(img, (x2, y2), 5, (0, 0, 255), -1)
        
        # Error line (white)
        cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 1)

    cv2.imwrite(img_name, img)
    print("Saved image with reprojection error: ", img_name[23:])

def JosepBosch(calibrate, board, camera_matrix, dist_coeffs, rvecs, tvecs, charucoCorners, charucoIds):
    #Compute mean of reprojection error
    tot_error=0
    total_points=0
    tot_error_list=[]
    total_points_list=[]
    lessErrorImages=[]
    obj_points = [board.getChessboardCorners()[i.flatten()] for i in charucoIds]
    #print("obj points", obj_points)
    img_points = charucoCorners.copy()
    image_files = [os.path.join(PATH_TO_YOUR_IMAGES, f) for f in os.listdir(PATH_TO_YOUR_IMAGES) if f.endswith(".png")]
    
    if(calibrate=="paired" or calibrate=="ela"):
        image_files.sort(key=lambda x: x.replace(".png", "\\"))
    else:
        image_files.sort()
    print("image files", image_files)
    for i in range(len(obj_points)):
        reprojected_points, _ = cv2.projectPoints(obj_points[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs)
        
        reprojected_points=reprojected_points.reshape(-1,2)

        tot_error_list.append(-tot_error)
        total_points_list.append(-total_points)
        tot_error+=np.sum(np.abs(img_points[i].reshape(-1, 2)-reprojected_points)**2)
        total_points+=len(obj_points[i])
        tot_error_list[-1]+=tot_error
        total_points_list[-1]+=total_points
        tot_error_list[-1]=np.sqrt(tot_error_list[-1]/total_points_list[-1])
        if(tot_error_list[-1]<4):
            lessErrorImages.append(image_files[i])
        projectPoints(charucoIds[i], charucoCorners[i], image_files[i], camera_matrix, dist_coeffs, rvecs[i], tvecs[i], board)
    print("These images have error less than 2", lessErrorImages)
    print(tot_error_list)
    ax=sns.scatterplot(data={"tot_error": tot_error_list, "total_points":total_points_list}, x="total_points", y="tot_error")
    for i, txt in enumerate(image_files):
        if tot_error_list[i] < math.ceil(min(tot_error_list)):
            ax.annotate(txt[txt.rindex("\\"):], (total_points_list[i], tot_error_list[i]))
    plt.show()
    mean_error=np.sqrt(tot_error/total_points)
    print("Mean reprojection error v1: ", mean_error)
    print("Mean reprojection error v2: ", np.mean(tot_error_list))