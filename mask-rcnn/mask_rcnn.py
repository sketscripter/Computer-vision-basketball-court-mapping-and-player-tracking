# USAGE
# python mask_rcnn.py --mask-rcnn mask-rcnn-coco --image images/example_01.jpg
# python mask_rcnn.py --mask-rcnn mask-rcnn-coco --image images/example_03.jpg --visualize 1

# import the necessary packages
import numpy as np
import argparse
import random
import time
import cv2
import os

# construct the argument parse and parse the arguments


# load the COCO class labels our Mask R-CNN was trained on
labelsPath = os.path.sep.join(["mask-rcnn-coco","object_detection_classes_coco.txt"])
LABELS = open(labelsPath).read().strip().split("\n")

# load the set of colors that will be used when visualizing a given instance segmentation
# colorsPath = os.path.sep.join(["mask-rcnn-coco", "colors.txt"])
# COLORS = open(colorsPath).read().strip().split("\n")
RED_COLOR = np.array([255, 0, 0]) 
BLACK_COLOR = np.array([255, 255, 255]) 

# derive the paths to the Mask R-CNN weights and model configuration
weightsPath = os.path.sep.join(["mask-rcnn-coco", "frozen_inference_graph.pb"])
configPath = os.path.sep.join(["mask-rcnn-coco", "mask_rcnn_inception_v2_coco_2018_01_28.pbtxt"])

# load our Mask R-CNN trained on the COCO dataset (90 classes) from disk
print("[INFO] loading Mask R-CNN from disk...")
net = cv2.dnn.readNetFromTensorflow(weightsPath, configPath)

# load our input image and grab its spatial dimensions
image = cv2.imread("images/basketball.jpg", cv2.IMREAD_UNCHANGED)
(H, W) = image.shape[:2]
print("[INFO] image size: {}x{} pixels".format(W, H))

# construct a blob from the input image and then perform a forward
# pass of the Mask R-CNN, giving us (1) the bounding box coordinates
# of the objects in the image along with (2) the pixel-wise segmentation
# for each specific object
blob = cv2.dnn.blobFromImage(image, swapRB=True, crop=False)
net.setInput(blob)

start = time.time()
(boxes, masks) = net.forward(["detection_out_final", "detection_masks"])
end = time.time()

# show timing information and volume information on Mask R-CNN
print("[INFO] Mask R-CNN took {:.6f} seconds".format(end - start))
print("[INFO] boxes shape: {}".format(boxes.shape))
print("[INFO] boxes size: {}".format(boxes.size))
print("[INFO] masks shape: {}".format(masks.shape))

# loop over the number of detected objects
for i in range(0, boxes.shape[2]):

	# extract the class ID of the detection along with the confidence
	# (i.e., probability) associated with the prediction
	classID = int(boxes[0, 0, i, 1])
	confidence = boxes[0, 0, i, 2]

	# filter out weak predictions by ensuring the detected probability
	# is greater than the minimum probability
	if confidence >0.5:
		# clone our original image so we can draw on it
		# clone = image.copy()

		# scale the bounding box coordinates back relative to the
		# size of the image and then compute the width and the height
		# of the bounding box
		box = boxes[0, 0, i, 3:7] * np.array([W, H, W, H])
		(startX, startY, endX, endY) = box.astype("int")
		boxW = endX - startX
		boxH = endY - startY

		# extract the pixel-wise segmentation for the object, resize
		# the mask such that it's the same dimensions of the bounding
		# box, and then finally threshold to create a *binary* mask
		mask = masks[i, classID]
		mask = cv2.resize(mask, (boxW, boxH), interpolation = cv2.INTER_NEAREST)
		mask = (mask > 0.3)

		# extract the ROI of the image
		roi = image[startY:endY, startX:endX]

		# check to see if are going to visualize how to extract the masked region itself
		if 1 > 0:
			# convert the mask from a boolean to an integer mask with
			# to values: 0 or 255, then apply the mask
			visMask = (mask * 255).astype("uint8")
			instance = cv2.bitwise_and(roi, roi, mask=visMask)

			# show the extracted ROI, the mask, along with the segmented instance
			# cv2.imshow("ROI", roi)
			# cv2.imshow("Mask", visMask)
			# cv2.imshow("Segmented", instance)

			# write the segmented image to disk
			cv2.imwrite("output/segmented{}.png".format(i), instance)
			
		# now, extract *only* the masked region of the ROI by passing in the boolean mask array as our slice condition
		roi = roi[mask]

		# Red will be used to visualize this particular instance segmentation 
		# then create a transparent overlay by blending the randomly selected color with the ROI
		blended = ((0.4 * RED_COLOR) + (0.6 * roi)).astype("uint8")

		# store the blended ROI in the original image
		image[startY:endY, startX:endX][mask] = blended

		# draw the bounding box of the instance on the image
		cv2.rectangle(image, (startX, startY), (endX, endY), (255,255,255), 2)

		# draw the predicted label and associated probability of the instance segmentation on the image
		text = "{}: {:.4f}".format("Person", confidence)
		cv2.putText(image, text, (startX, startY - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

		# show the output image
		# cv2.imshow("Output", image)
		# cv2.waitKey(0)

	cv2.imwrite("output/result.jpg", image)		
