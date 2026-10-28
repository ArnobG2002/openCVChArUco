import cv2
import os
import numpy as np
import json1
import raw
import argparse
from core import TransInv, RpToTrans
import seaborn as sns
import matplotlib.pyplot as plt 
import project_points
import shutil
# ------------------------------
# ENTER YOUR REQUIREMENTS HERE:
ARUCO_DICT = cv2.aruco.DICT_4X4_250

SQUARE_LENGTH = 10
MARKER_LENGTH = 7

print("We are using openCV version", cv2.__version__)

def TransfInv(rvec, tvec):
    """
    Inverts a homogeneous transformation matrix

    :param rvec: A rotation vector (3x1) representing the rotation part of the transformation matrix.
    :param tvec: A translation vector (3x1) representing the translation part of the transformation matrix.
    :return: The inverse of the transformation matrix
    """
    T1=RpToTrans(cv2.Rodrigues(rvec)[0], tvec)
    np.testing.assert_allclose([np.dot(T1[:, 0], T1[:, 1]), np.dot(T1[:, 1], T1[:, 2]), np.dot(T1[:, 2], T1[:, 0])], [0, 0, 0], atol=1e-15, err_msg="The rotation part is not valid.")
    return TransInv(T1)


def Transf_to_UpLookatEye(tmat, up_in_cameraFrame, looking_direction_in_cameraFrame):
    """
    Convert a transformation matrix to a look-at vector, an up vector and an eye vector. 
    :param tmat: The transformation matrix representing transformation of camera{c1} in reference to some frame {c2}.
    :param up_in_cameraFrame: The up vector in the camera frame {c1}.
    :param looking_direction_in_cameraFrame: The looking direction vector in the camera frame {c1}.

    :return: A 3x3 matrix where the first column is the up vector, the second column is the lookat point, and the third column is the eye point, all in the reference frame {c2}.
    """
    up=tmat[:3,:3]@up_in_cameraFrame
    looking_direction=tmat[:3,:3]@looking_direction_in_cameraFrame

    np.testing.assert_almost_equal(np.dot(looking_direction.flatten(), up.flatten()), 0, err_msg="Up and looking direction are not orthogonal.")

    return np.concatenate([up, tmat[:3, 3:4]+looking_direction, tmat[:3, 3:4]], axis=1)

def generateCharuco(columns, rows, square_length, marker_length, ratio):
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)

    # We have to input the size of a square and the size of a marker in the second and third argument.
    # There are two ways to measure the size of a square: 
    #          either measure the size of one square, 
    #          or measure the size of a side of the board and divide it by the number of squares on that side. 
    # In which unit you will measure is completely your choice but just keep in mind that the translation vectors from OpenCV or the `Eye` output from the scripts in this project will be in the same unit of measurement.
    # For with the measure you use it will be measured back to you. (Luke 6:38)
    board = cv2.aruco.CharucoBoard((columns, rows), square_length, marker_length, dictionary)

    if(ratio=='letter'):
        img = cv2.aruco.CharucoBoard.generateImage(board, (3300, 2550), marginSize=802)
        cv2.imwrite("charuco_3300_2550_802.png", img)
    elif(ratio=='lg16'):
        img = cv2.aruco.CharucoBoard.generateImage(board, (3840, 2160), marginSize=240)
        cv2.imwrite("charuco_3840_2160_240.png", img)

def drawDetectedCornersCharuco(img, corners, ids):
    """
    Draw rectangles and IDs to the corners, wrapper

    Parameters
    ----------
    img : numpy.array()
        Two dimensional image matrix. Image can be grayscale image or RGB image
        including 3 layers. Allowed shapes are (x, y, 1) or (x, y, 3).
    corners : numpy.array()
        Checkerboard corners.
    ids : numpy.array()
        Corners' IDs.
    """
    if ids.size > 0:
        id_color = (255, 255, 0)
        # corners = corners.reshape((corners.shape[0], 1, corners.shape[1]))
        # ids = ids.reshape((ids.size, 1))
        cv2.aruco.drawDetectedCornersCharuco(img, corners, ids, id_color)
def process_calibration_results(calibrate, board, all_charuco_corners, all_charuco_ids):
    
    camera_matrix = np.load('camera_matrix.npy')
    dist_coeffs = np.load('dist_coeffs.npy')
    rvecs = np.load('rvecs.npy')
    tvecs = np.load('tvecs.npy')
    json1.writeDistortion(dist_coeffs.flatten())
    project_points.JosepBosch(calibrate, board, camera_matrix, dist_coeffs, rvecs, tvecs, all_charuco_corners, all_charuco_ids)

    
    print( '\n Camera Matrix', camera_matrix, '\n', "Distortion coeff", dist_coeffs, '\n RVec', rvecs, '\n TVec', tvecs, '\n Rotation Matrix', cv2.Rodrigues(rvecs[0])[0])
    # print('Translation of the camera in reference to the Charuco', -cv2.Rodrigues(rvecs[0])[0].T @ tvecs[0])
    # print('Rotation of the camera in reference to the Charuco', cv2.Rodrigues(rvecs[0])[0].T)

    World_to_ChArUco=np.array([ [1, 0, 0,  0],
                                [0, -1, 0, 0],
                                [0, 0, -1, 0],
                                [0, 0, 0,  1]
                              ])


    assert len(rvecs) == len(tvecs), "The rotation vector and translation vector must have the same length."
    for i in range(len(rvecs)):
        #print('\n', image_files[i], '\n', World_to_ChArUco[:3,:3]@Transf_to_UpLookatEye(TransfInv(rvecs[i], tvecs[i]), [[0], [-1], [0]], [[0], [0], [1]]), '\n')
        json1.writeUpLookatEye(camera_matrix, calibrate, i, World_to_ChArUco[:3,:3]@Transf_to_UpLookatEye(TransfInv(rvecs[i], tvecs[i]), [[0], [-1], [0]], [[0], [0], [1]]))
    # Iterate through displaying all the images
    # Load PNG images from folder
    image_files = json1.getImageFiles(calibrate)
    for image_file in image_files:
        image = raw.raw_to_npArray(image_file) if(calibrate=="images" or calibrate=="paired" or calibrate=="ela") else cv2.imread(image_file)
        undistorted_image = cv2.undistort(image, camera_matrix, dist_coeffs)
        # cv2.imshow('Undistorted Image', undistorted_image)
        # cv2.waitKey(0)
        if calibrate=="paired" or calibrate=="ela":
            cv2.imwrite("undistorted_images/"+image_file[image_file.index("\\"):image_file.rindex("\\")]+".png", undistorted_image)
        else:
            cv2.imwrite("undistorted_images/"+image_file[21:-4]+".png", undistorted_image)
def calibrate_and_save_parameters(calibrate):
    # Define the aruco dictionary and charuco board
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)

    # We have to input the size of a square and the size of a marker in the second and third argument.
    # There are two ways to measure the size of a square: 
    #          either measure the size of one square, 
    #          or measure the size of a side of the board and divide it by the number of squares on that side. 
    # In which unit you will measure is completely your choice but just keep in mind that the translation vectors from OpenCV or the `Eye` output from the scripts in this project will be in the same unit of measurement.
    # For with the measure you use it will be measured back to you. (Luke 6:38)
    board = cv2.aruco.CharucoBoard((14, 7), 341.4/16, (341.4/16)*0.7, dictionary) 

    params = cv2.aruco.DetectorParameters()

    image_files = json1.getImageFiles(calibrate)
    all_charuco_corners = []
    all_charuco_ids = []
    every_charuco_ids_len =[]
    
    # বিধ্বংসই নবনির্মাণের কারণ, পার্থ।
    # উদ্ভিদের একটি শাখা কর্তন করলে আরেকটি শাখার জন্ম হয়।
    # তুমি আজকের বিদ্ধংস নিয়ে কেন ভয়ভীত হচ্ছ?
    # কাল পুনঃ নবনির্মাণ হবে এ সত্য কি জানো না?
    if os.path.exists("./detectedMarkersDrawn"):
        shutil.rmtree('./detectedMarkersDrawn')
    if os.path.exists("./undistorted_images"):
        shutil.rmtree('./undistorted_images')
    
    os.makedirs("./detectedMarkersDrawn")
    os.makedirs("./undistorted_images")
    
    for i, image_file in enumerate(image_files):
        image = raw.raw_to_npArray(image_file) if(calibrate=="images" or calibrate=="paired" or calibrate=='ela') else cv2.imread(image_file)
        #image=cv2.imread(image_file)
        #print("I am reading image of length", image.shape)
        #print(image.shape, Image.open("0.png").size)
        image_copy = image.copy()
        #image_copy=cv2.cvtColor(image_copy, cv2.COLOR_BGR2GRAY)
        # cv2.imshow("meh", image_copy)
        # cv2.waitKey(0)
        marker_corners=[]
        marker_ids=np.array([])
        marker_corners, marker_ids, _= cv2.aruco.detectMarkers(image, dictionary, parameters=params)

        #marker_corners1, marker_ids1, _= cv2.aruco.detectMarkers(image_rawpy, dictionary, parameters=params)

        # print(marker_corners)
        #print(marker_ids)
        print('reading', image_file)
        print(len(marker_corners)==len(marker_ids), len(marker_ids)==60)
        
        # If at least one marker is detected
        if len(marker_ids) > 0:
            cv2.aruco.drawDetectedMarkers(image_copy, marker_corners, marker_ids)
            
            
            #board.setLegacyPattern(True)
            #print('\n marker corners \n', marker_corners, '\n marker ids \n', marker_ids)
            charuco_retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(marker_corners, marker_ids, image, board)
            #print('retval', charuco_retval, 'charuco ids length', charuco_ids)
            drawDetectedCornersCharuco(image_copy, charuco_corners,
                                   charuco_ids)
            if(calibrate=="paired" or calibrate=="ela"):
                cv2.imwrite("detectedMarkersDrawn/"+image_files[i][image_files[i].index("\\"):image_files[i].rindex("\\")]+".png", image_copy)
            else:
                cv2.imwrite("detectedMarkersDrawn/"+image_files[i][image_files[i].rindex("\\"):-4]+".png", image_copy)
            print('done drawing')
            if charuco_retval:
                all_charuco_corners.append(charuco_corners)
                all_charuco_ids.append(charuco_ids)
                every_charuco_ids_len.append(len(charuco_ids))
    # if(calibrate=="images"):
    #     np.save('all_charuco_corners_images.npy', all_charuco_corners)
    #     np.save('all_charuco_ids_images.npy', all_charuco_ids)
    
    good_images=[]
    for i in range(len(image_files)):
        if(every_charuco_ids_len[i]>=70):
            good_images.append(image_files[i])
    if calibrate!="paired":
        sns.barplot({"image": list(map(lambda x:x[x.index("\\"): -4],image_files)), "number of corners detected": every_charuco_ids_len}, x="image", y="number of corners detected")
        plt.show()
    # Calibrate camera
    #print("\n All ChAruCo ids \n", all_charuco_ids, "\n All ChArUco corners \n", all_charuco_corners)
    retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(all_charuco_corners, all_charuco_ids, board, image.shape[1::-1], None, None)
    np.save('camera_matrix.npy', camera_matrix)
    np.save('dist_coeffs.npy', dist_coeffs)
    np.save('rvecs.npy', rvecs)
    np.save('tvecs.npy', tvecs)
    process_calibration_results(calibrate, board, all_charuco_corners, all_charuco_ids)
def detect_pose(i, camera_matrix, dist_coeffs, calibrate):
    # Undistort the image
    image_files = json1.getImageFiles(calibrate)
    print("reading", image_files[i])
    image = raw.raw_to_npArray(image_files[i]) if (calibrate=="images" or calibrate=="paired" or calibrate=="ela") else cv2.imread(image_files[i])
    image_copy = image.copy()
    undistorted_image = cv2.undistort(image, camera_matrix, dist_coeffs)

    # Define the aruco dictionary and charuco board
    
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)

    # We have to input the size of a square and the size of a marker in the second and third argument.
    # There are two ways to measure the size of a square: 
    #          either measure the size of one square, 
    #          or measure the size of a side of the board and divide it by the number of squares on that side. 
    # In which unit you will measure is completely your choice but just keep in mind that the translation vectors from OpenCV or the `Eye` output from the scripts in this project will be in the same unit of measurement.
    # For with the measure you use it will be measured back to you. (Luke 6:38)
    board = cv2.aruco.CharucoBoard((14, 7), 341.4/16, (341.4/16)*0.7, dictionary)

    params = cv2.aruco.DetectorParameters()

    # Detect markers in the undistorted image
    marker_corners, marker_ids, _ = cv2.aruco.detectMarkers(undistorted_image, dictionary, parameters=params)
    
    # If at least one marker is detected
    if len(marker_ids) > 0:
        cv2.aruco.drawDetectedMarkers(image_copy, marker_corners, marker_ids)
        # Interpolate CharUco corners
        charuco_retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(marker_corners, marker_ids, undistorted_image, board)
        #print('charuco ids', charuco_ids)
        drawDetectedCornersCharuco(image_copy, charuco_corners, charuco_ids)
        if(calibrate=="paired" or calibrate=="ela"):
            cv2.imwrite("detectedMarkersDrawn/"+image_files[i][image_files[i].index("\\"):image_files[i].rindex("\\")]+".png", image_copy)
        else:
            cv2.imwrite("detectedMarkersDrawn/"+image_files[i][image_files[i].rindex("\\"):-4]+".png", image_copy)
        # If enough corners are found, estimate the pose
        if charuco_retval:
            retval, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(charuco_corners, charuco_ids, board, camera_matrix, dist_coeffs, None, None)
            return rvec, tvec, charuco_corners, charuco_ids
    return None
def detectPoseCharucoBoard(calibrate):
    # Load the camera matrix and distortion coefficients
    camera_matrix = np.load('camera_matrix.npy')
    dist_coeffs = np.load('dist_coeffs.npy')
    print( '\n Camera Matrix', camera_matrix, '\n', "Distortion coeff", dist_coeffs)
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)

    # We have to input the size of a square and the size of a marker in the second and third argument.
    # There are two ways to measure the size of a square: 
    #          either measure the size of one square, 
    #          or measure the size of a side of the board and divide it by the number of squares on that side. 
    # In which unit you will measure is completely your choice but just keep in mind that the translation vectors from OpenCV or the `Eye` output from the scripts in this project will be in the same unit of measurement.
    # For with the measure you use it will be measured back to you. (Luke 6:38)
    board = cv2.aruco.CharucoBoard((14, 7), 341.4/16, (341.4/16)*0.7, dictionary)

    all_charuco_corners = []
    all_charuco_ids = []
    rvecs = []
    tvecs = []

    # বিধ্বংসই নবনির্মাণের কারণ, পার্থ।
    # উদ্ভিদের একটি শাখা কর্তন করলে আরেকটি শাখার জন্ম হয়।
    # তুমি আজকের বিদ্ধংস নিয়ে কেন ভয়ভীত হচ্ছ?
    # কাল পুনঃ নবনির্মাণ হবে এ সত্য কি জানো না?
    shutil.rmtree('./detectedMarkersDrawn')
    shutil.rmtree('./undistorted_images')
    
    if not os.path.exists("./detectedMarkersDrawn"):
        os.makedirs("./detectedMarkersDrawn")
    if not os.path.exists("./undistorted_images"):
        os.makedirs("./undistorted_images")

    print('image files', json1.getImageFiles(calibrate))
    for i in range(len(json1.getImageFiles(calibrate))):
        rvec, tvec, charuco_corners, charuco_ids=detect_pose(i, camera_matrix, dist_coeffs, calibrate)
        all_charuco_corners.append(charuco_corners)
        all_charuco_ids.append(charuco_ids)
        rvecs.append(rvec)
        tvecs.append(tvec)
    np.save('camera_matrix.npy', camera_matrix)
    np.save('dist_coeffs.npy', dist_coeffs)
    np.save('rvecs.npy', rvecs)
    np.save('tvecs.npy', tvecs)
    process_calibration_results(calibrate, board, all_charuco_corners, all_charuco_ids)   

def compareMarkerCorners(marker_corners, marker_corners1):
    for i in range(17):
        if(np.allclose(marker_corners[i] , marker_corners1[i])):
            print('rgb and bgr gives same result')
        else:
            print('rgb and bgr gives different results')
            print('bgr gives:', marker_corners[i], '\n', 'rgb gives:', marker_corners1[i])
#calibrate_and_save_parameters()
parser = argparse.ArgumentParser(description="Camera calibration script")
parser.add_argument("--generate", action='store_true', help='generate ChArUco')
parser.add_argument("--columns", type=int)
parser.add_argument("--rows", type=int)
parser.add_argument("--square_length", type=float)
parser.add_argument("--marker_length", type=float)
parser.add_argument("--ratio", type=str)
parser.add_argument("--calibrate", type=str, help='calibrate images or colors')
args = parser.parse_args()
if(args.generate):
    generateCharuco(args.columns, args.rows, args.square_length, args.marker_length, args.ratio)
elif(args.calibrate):
    if(os.path.exists("./camera_matrix.npy") and os.path.exists("./dist_coeffs.npy")):
        detectPoseCharucoBoard(args.calibrate)
    else:
        calibrate_and_save_parameters(args.calibrate)
