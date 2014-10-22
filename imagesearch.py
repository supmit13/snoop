# -*- coding: utf-8 -*-

import os, sys, re, time
import cv2, numpy
from pyimagesearch import imutils
import argparse, cPickle, glob
from matplotlib import pyplot as plt


IMGEXTS = ("tif", "tiff", "gif", "jpeg", "jpg", "png", "bmp", "svg")
"""
If chi-squared distance between 2 images is less than this value, then they are
considered to be similar. (An exact match will have a value of 0).
"""
MIN_CHI_SQUARED_DISTANCE = 1

# TO DO: Need to set the value of this variable appropriately. Also need
# to choose one of the methods for computing the containment cases.
THRESHOLD = 0.40

# Threshold count used in FLANN based matcher function. If the number of
# matches exceed this count, then the function concludes that a successful
# match exists. Otherwise, it concludes that a match doesn't exist and
# returns 'None' from the FLANN based matcher function.
MIN_MATCH_COUNT = 25

# TO DO: Need to identify the Hessian threshold appropriately so that the
# SURF keypoint identification is efficient.
HESSIAN_THRESHOLD = 400

FLANN_INDEX_KDTREE = 0


class RGBHistogram:
    def __init__(self, bins):
        self.bins = bins
 
    def describe(self, image):
        """
        compute a 3D histogram in the RGB colorspace,
        then normalize the histogram so that images
        with the same content, but either scaled larger
        or smaller will have (roughly) the same histogram
        """
        hist = cv2.calcHist([image], [0, 1, 2],None, self.bins, [0, 256, 0, 256, 0, 256])
        hist = cv2.normalize(hist)
        # return out 3D histogram as a flattened array
        return hist.flatten()


"""
********************** Utility functions **********************
"""
def checkImages(imglist):
    """
    This function checks the sanity of the list of image files passed
    to it as a list parameter.  Returns a list of sanitized image files.
    """
    sanitizedlist = []
    imgcount=imglist.__len__()
    for img in imglist:
        if not os.path.exists(img):
            print "File '%s' doesn't exist\n"%img
            continue
        extmatch = False
        for ext in IMGEXTS:
            extpattern = re.compile(ext+"$", re.IGNORECASE)
            if re.search(extpattern, img):
                extmatch = True
                break
        if not extmatch:
            print "Invalid image extension for file '%s'\n"%img
            continue
        sanitizedlist.append(img)
    return(sanitizedlist)


def toGrayShade(img):
    """
    Function to convert the image file passed as the only argument to grey shade. It will
    return the file which gets created with the image in grey shade. This will be used to
    pre-process images in various image matching functions (listed below).
    """
    return(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))


def createImageIndex(imagesdir):
    """
    Function to create an index for all image files found in the directory passed to it as
    an argument.
    """
    index = {}
    desc = RGBHistogram([8, 8, 8])
    allfiles = glob.glob(imagesdir + os.path.sep + "*.*")
    allimagefiles = checkImages(allfiles)
    for imgfile in allimagefiles:
        image = cv2.imread(imgfile)
        features = desc.describe(image)
        index[imgfile] = features
    return(index)


def chi2_distance(histA, histB, eps = 1e-10):
    """
    compute the chi-squared distance
    """
    d = 0.5 * numpy.sum([((a - b) ** 2) / (a + b + eps) for (a, b) in zip(histA, histB)])
    return d


def drawMatches(img1, kp1, img2, kp2, matches):
    """
    This function takes in two images with their associated 
    keypoints, as well as a list of DMatch data structure (matches) 
    that contains which keypoints matched in which images.
    An image will be produced where a montage is shown with
    the first image followed by the second image beside it.
    Keypoints are delineated with circles, while lines are connected
    between matching keypoints.

    img1,img2 - Grayscale images
    kp1,kp2 - Detected list of keypoints through any of the OpenCV keypoint 
              detection algorithms
    matches - A list of matches of corresponding keypoints through any
              OpenCV keypoint matching algorithm
    """

    # Create a new output image that concatenates the two images together
    # (a.k.a) a montage
    rows1 = img1.shape[0]
    cols1 = img1.shape[1]
    rows2 = img2.shape[0]
    cols2 = img2.shape[1]

    out = numpy.zeros((max([rows1,rows2]),cols1+cols2,3), dtype='uint8')

    # Place the first image to the left
    out[:rows1,:cols1,:] = numpy.dstack([img1, img1, img1])

    # Place the next image to the right of it
    out[:rows2,cols1:cols1+cols2,:] = numpy.dstack([img2, img2, img2])

    # For each pair of points we have between both images
    # draw circles, then connect a line between them
    for mat in matches:

        # Get the matching keypoints for each of the images
        img1_idx = mat.queryIdx
        img2_idx = mat.trainIdx

        # x - columns
        # y - rows
        (x1,y1) = kp1[img1_idx].pt
        (x2,y2) = kp2[img2_idx].pt

        # Draw a small circle at both co-ordinates
        # radius 4
        # colour blue
        # thickness = 1
        cv2.circle(out, (int(x1),int(y1)), 4, (255, 0, 0), 1)   
        cv2.circle(out, (int(x2)+cols1,int(y2)), 4, (255, 0, 0), 1)

        # Draw a line in between the two points
        # thickness = 1
        # colour blue
        cv2.line(out, (int(x1),int(y1)), (int(x2)+cols1,int(y2)), (255, 0, 0), 1)


    # Show the image
    cv2.imshow('Matched Features', out)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


"""
********************* Functions to match 2 given images ***********************
"""

# TO DO: Need to choose a method to compute the containment matching case.
def matchContainments(img1, img2, method):
    """
    This function will check if image in img1 is contained in the image in file img2. img1
    is the query image and img2 is the target.
    """
    im1 = cv2.imread(img1)
    im2 = cv2.imread(img2)
    grayim1 = toGrayShade(im1)
    grayim2 = toGrayShade(im2)
    match = cv2.matchTemplate(grayim1, grayim2, method)

    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(match)
    matchLoc = minLoc
    #print minLoc, maxLoc
    #print minVal, maxVal
    if method == cv2.TM_SQDIFF_NORMED:
        if minVal <= THRESHOLD:
            return(True)
        else:
            return(False)
    elif method == cv2.TM_CCORR_NORMED:
        if maxVal >= THRESHOLD:
            return(True)
        else:
            return(False)


def matchedCentreOffset(img1, img2):
    im1 = cv2.imread(img1)
    im2 = cv2.imread(img2)
    grayim1 = toGrayShade(im1)
    grayim2 = toGrayShade(im2)
    match = cv2.matchTemplate(grayim1, grayim2, cv2.cv.CV_TM_SQDIFF_NORMED)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(match)
    if minVal <= THRESHOLD:
        minLocXPoint, minLocYPoint = minLoc
        im1row, im1col = grayim1.shape[:2]
        centerPoint = (minLocXPoint + int(im1row/2), minLocYPoint + int(im1col/2))
        return(centerPoint)
    else:
        return (None)
    

def matchPixelShifts(img1, img2):
    """
    This function will check if the image in file img1 is a transpose of the image in file
    img2. (img1 is the query image and img2 is the target.)
    """
    pass


def matchShadeDiffs(img1, img2):
    """
    This function will check if the images in files img1 and img2 differ in shades only.
    It will return true if the images are identical but have different shades. img1 is
    the query image and img2 is the target. 
    """
    pass


def colourHistograms(img1, img2, index):
    """
    This will check the RGB Histograms of the images and try to find if the images are similar.
    Will be used to identify dissimilar images in order to eliminate them. img1 is the query
    image and img2 is the target. Returns the chi-squared distance between the 2 images. The
    return value (d) is 0 for an exact match. Works well for images that are identical. Even
    the color should be same.
    """
    results = {}
    desc = RGBHistogram([8, 8, 8])
    queryimage = cv2.imread(img1) # This is our query image.
    queryfeatures = desc.describe(queryimage)
    targetfeatures = index[img2]
    d = chi2_distance(targetfeatures, queryfeatures)
    return(d)


def cornerDetectionMatches(img1, img2):
    """
    This will try to identify corners in each of the 2 given images. If the number of corners
    in each of the 2 images are NOT the same, then we eliminate the target image. This will
    serve the purpose of a preliminary filter which will eliminate obviously dissimilar images.
    img1 is the query image and img2 is the target. (This uses the cv2.goodFeaturesToTrack()
    method - https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_feature2d/py_fast/py_fast.html)
    """
    pass


def matchKeyPointsSURF(img1, img2):
    """
    This will identify keypoints (using SURF) in both images and match them to find similarities.
    https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_feature2d/py_surf_intro/py_surf_intro.html
    https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_feature2d/py_brief/py_brief.html
    """
    image1 = cv2.imread(img1)
    image2 = cv2.imread(img2)
    grayimg1 = toGrayShade(image1)
    grayimg2 = toGrayShade(image2)
    
    surf = cv2.SURF(HESSIAN_THRESHOLD)
    surf.upright = True
    if surf.descriptorSize() == 64:
        surf.extended = True
    kp1, des1 = surf.detectAndCompute(grayimg1, None)
    kp2, des2 = surf.detectAndCompute(grayimg2, None)
    #print kp1
    #print des1.shape
    #print kp2
    #print des2.shape
    #kp, des = surf.detectAndCompute()


def FLANNMatcher(img1, img2):
    """
    FLANN based matcher function. img1 is the query image and img2 is the target.
    https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_feature2d/py_matcher/py_matcher.html.
    The variable MIN_MATCH_COUNT defines the threshold count of the matches, exceeding which one can say that a
    satisfactory match exists. Otherwise, we simply print a message to the effect that a match couldn't be found
    and return 'False' from the function.
    """
    image1 = cv2.imread(img1, 0)
    image2 = cv2.imread(img2, 0)

    sift = cv2.SIFT()
    kp_query, des_query = sift.detectAndCompute(image1, None)
    kp_target, des_target = sift.detectAndCompute(image2, None)

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des_query, des_target, k=2)

    goodmatches = []

    for i, (m,n) in enumerate(matches):
        if m.distance < 0.7 * n.distance:
            goodmatches.append(m)
            
    if len(goodmatches) > MIN_MATCH_COUNT:
        src_pts = numpy.float32([ kp_query[m.queryIdx].pt for m in goodmatches ]).reshape(-1,1,2)
        dst_pts = numpy.float32([ kp_target[m.trainIdx].pt for m in goodmatches ]).reshape(-1,1,2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        matchesMask = mask.ravel().tolist()

        h,w = image1.shape
        pts = numpy.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        dst = cv2.perspectiveTransform(pts,M)
        return (True)
    else:
        print "Not enough matches are found - %d/%d" % (len(goodmatches),MIN_MATCH_COUNT)
        matchesMask = None
        return(False)

    

def bruteforceMatcher(img1, img2, desctype='SIFT'):
    """
    Brute force matcher with desctype descriptors. img1 is query image, img2 is the target.
    https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_feature2d/py_matcher/py_matcher.html
    Handles the case using SIFT and SURF for keypoints and descriptors identificatiion.
    TO DO: Throws error if executed with ORB - 'cv2.DMatch object is not iterable.' This needs to
    be rectified.
    """
    image1 = cv2.imread(img1)
    image2 = cv2.imread(img2)

    kp_query, des_query = None, None
    desc = None
    if desctype == 'ORB':
        desc = cv2.ORB()
    elif desctype == 'SIFT':
        desc = cv2.SIFT()
        image1 = cv2.imread(img1, 0)
        image2 = cv2.imread(img2, 0)
    else:
        print "Descriptor method not supported.\n"
        return(None)
    if desctype == 'ORB':
        #image2.resize(image1.shape[1], image1.shape[0])
        kp_query, des_query = desc.detectAndCompute(image1, None)
        kp_target, des_target = desc.detectAndCompute(image2, None)
    elif desctype == 'SIFT':
        kp_query, des_query = desc.detectAndCompute(image1, None)
        kp_target, des_target = desc.detectAndCompute(image2, None)
    try:
        if desctype == 'ORB':
            bfmatcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bfmatcher.match(des_query, des_target)
            matches = sorted(matches, key=lambda x:x.distance)
        elif desctype == 'SIFT':
            bfmatcher = cv2.BFMatcher()
            matches = bfmatcher.knnMatch(des_query, des_target, k=2)
        if desctype == 'ORB':
            good = []
            for m,n in matches:
                if m.distance < 0.75*n.distance:
                    good.append([m])
            if matches.__len__() >= 10:
                #print matches.__len__()
                return matches.__len__()
        elif desctype == 'SIFT':
            good = []
            for m,n in matches:
                #print m.distance, 0.75*n.distance
                if m.distance < 0.75*n.distance:
                    good.append([m])
            if good.__len__() >= 10:
                #print good.__len__()
                return True
            else:
                return False
    except:
        print "Error: %s\n"%sys.exc_info()[1].__str__()
        return(None)
    


def homographyMatcher(img1, img2):
    """
    Image matching using Homography - img1 is the query image and img2 is the target.
    https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_feature2d/py_feature_homography/py_feature_homography.html
    This function performs a FLANN based match to find SIFT features. It stores the 'good' points as per Lowe's ratio test. If enough
    matches are found, it extracts the locations of the keypoints from both images. These are used to find the transformation matrix.
    Using the transformation matrix, the corners of the query image are transformed to corresponding  points in the target image.
    Note: Much of the code in this function is same as the code in the 'FLANNMatcher' function. Hence, we could have implemented  it
    using a call to 'FLANNMatcher', but we did not do so in order to keep the code independent of one another. Thus, we would be able to
    change one of these functions without affecting the other.
    """
    image1 = cv2.imread(img1, 0)
    image2 = cv2.imread(img2, 0)

    sift = cv2.SIFT()
    kp_query, des_query = sift.detectAndCompute(image1, None)
    kp_target, des_target = sift.detectAndCompute(image2, None)

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des_query, des_target, k=2)

    goodmatches = []

    for i, (m,n) in enumerate(matches):
        if m.distance < 0.7 * n.distance:
            goodmatches.append(m)
    if len(goodmatches)>MIN_MATCH_COUNT:
        src_pts = numpy.float32([ kp_query[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = numpy.float32([ kp_target[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        matchesMask = mask.ravel().tolist()
        h,w = img1.shape
        pts = numpy.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        dst = cv2.perspectiveTransform(pts,M)
        img2 = cv2.polylines(img2,[numpy.int32(dst)],True,255,3, cv2.LINE_AA)
    else:
        print "Not enough matches are found - %d/%d" % (len(goodmatches),MIN_MATCH_COUNT)
        matchesMask = None

    #draw_params = dict(matchColor = (0,0,255), singlePointColor = None, matchesMask=matchesMask, flags = 2)
    img3 = drawMatches(image1,kp_query,image2,kp_target,goodmatches)
    plt.imshow(img3, 'gray'),plt.show()




def faceDetectionHaarCascade(img1, img2):
    """
    Face detection using Haar cascade classifiers. img1 is the query image and img2 is the target.
    https://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_objdetect/py_face_detection/py_face_detection.html
    """
    pass



if __name__ == "__main__":
    image1 = sys.argv[1]
    image2 = sys.argv[2]
    # Check if the images exist
    imglist = checkImages(sys.argv[1:])
    iscontained1 = matchContainments(imglist[0], imglist[1], cv2.TM_SQDIFF_NORMED)
    if iscontained1:
        print "Image 2 contains image 1\n"
    print "Containment1 - " + iscontained1.__str__()
    iscontained2 = matchContainments(imglist[0], imglist[1], cv2.TM_CCORR_NORMED)
    print iscontained2
    if iscontained2:
        print "Image 2 contains image 1\n"
    print "Containment2 - " + iscontained2.__str__()
    indx = createImageIndex("/home/supriyo/work/Snoop/softwares/images")
    #d = colourHistograms("/home/supriyo/work/Snoop/softwares/images/XnG05.png", "/home/supriyo/work/Snoop/softwares/images/sd4QY.png", indx)
    #d = colourHistograms("/home/supriyo/work/Snoop/softwares/images/EYs9B.png", "/home/supriyo/work/Snoop/softwares/images/RyYor.png", indx)
    #d = colourHistograms("/home/supriyo/work/Snoop/softwares/images/starry_night.jpg", "/home/supriyo/work/Snoop/softwares/images/starry_night2.jpg", indx)
    #d = colourHistograms("/home/supriyo/work/Snoop/softwares/images/sd4QY.png", "/home/supriyo/work/Snoop/softwares/images/XnG05.png", indx)
    d = colourHistograms(imglist[0], imglist[1], indx)
    print "Distance in Colour Histogram: %s\n"%d.__str__()
    #matchKeyPointsSURF(imglist[0], imglist[1])
    #retval = bruteforceMatcher("/home/supriyo/work/Snoop/softwares/images/qh2Qm.png", "/home/supriyo/work/Snoop/softwares/images/4phVl.png", 'SIFT')
    #retval = bruteforceMatcher("/home/supriyo/work/Snoop/softwares/images/4kBWS.png", "/home/supriyo/work/Snoop/softwares/images/XHCXs.png", 'SIFT')
    retval = bruteforceMatcher(imglist[0], imglist[1], 'SIFT')
    if retval:
        print "Bruteforce: Images are similar\n"
    else:
        print "Bruteforce: Images are dissimilar\n"
    #retval = bruteforceMatcher("/home/supriyo/work/Snoop/softwares/images/ocean_of_peace_cosmic.jpg", "/home/supriyo/work/Snoop/softwares/images/whereiswaldo.jpg", 'SIFT')
    #print retval
    #FLANNMatcher("/home/supriyo/work/Snoop/softwares/images/RyYor.png", "/home/supriyo/work/Snoop/softwares/images/szqDb.png")
    #FLANNMatcher("/home/supriyo/work/Snoop/softwares/images/qh2Qm.png", "/home/supriyo/work/Snoop/softwares/images/4phVl.png")
    f = FLANNMatcher(imglist[0], imglist[1])
    if f:
        print "FLANN Matcher: Images are similar\n"
    else:
        print "FLANN Matcher: Images are dissimilar\n"
    h = homographyMatcher(imglist[0], imglist[1])
    
