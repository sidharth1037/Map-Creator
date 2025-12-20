import cv2
import numpy as np
import matplotlib.pyplot as plt

def get_skeleton(img_path):
    # 1. Load image
    img = cv2.imread(img_path, 0)
    if img is None:
        print("Error: Image not found.")
        return

    # 2. Gaussian Blur 
    # (Smoother than MedianBlur, helps keep weak connections intact)
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # 3. Binary Thresholding (Otsu)
    # Invert: Lines = White, Background = Black
    ret, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 4. Aggressive Morphological Closing
    # This fills gaps INSIDE the thick lines before we thin them.
    # Increased iterations to 4 to really solidify the black marker lines.
    kernel = np.ones((3,3), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=4)

    # 5. Robust Thinning Function (Zhang-Suen algorithm implementation)
    # This is more structure-preserving than standard erosion
    def thinning(img):
        # Create a copy to work on
        dst = img.copy() / 255
        prev = np.zeros(img.shape[:2], np.uint8)
        diff = None

        while True:
            dst = cv2.ximgproc.thinning(img, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN) if hasattr(cv2, 'ximgproc') else None
            
            # Fallback if ximgproc is not available (standard OpenCV manual thinning)
            if dst is None:
                size = np.size(img)
                skel = np.zeros(img.shape, np.uint8)
                element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
                done = False
                
                eroded = img.copy()
                while not done:
                    open_op = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, element)
                    temp = cv2.subtract(eroded, open_op)
                    eroded = cv2.erode(eroded, element)
                    skel = cv2.bitwise_or(skel, temp)
                    if cv2.countNonZero(eroded) == 0:
                        done = True
                return skel
            else:
                return dst

    # Run Thinning First Pass
    skeleton = thinning(closing)

    # 6. "Bridge" Micro-Gaps (The Fix for Broken Lines)
    # Dilate the skeleton slightly to connect pixels that are touching diagonally or 1px apart
    kernel_bridge = np.ones((3,3), np.uint8)
    bridged = cv2.dilate(skeleton, kernel_bridge, iterations=1)
    
    # Thin again to return to 1-pixel width
    final_skeleton = thinning(bridged)

    return img, closing, final_skeleton

# Run the function
original, binary, skeleton_result = get_skeleton('first plain clean.jpg')

# Visualization
plt.figure(figsize=(15, 5))
plt.subplot(131), plt.imshow(original, cmap='gray'), plt.title('Original')
plt.subplot(132), plt.imshow(binary, cmap='gray'), plt.title('Solid Binary (No Holes)')
plt.subplot(133), plt.imshow(skeleton_result, cmap='gray'), plt.title('Continuous Skeleton')
plt.show()

# Save
cv2.imwrite('skeleton.png', skeleton_result)
print("Saved improved skeleton.png")