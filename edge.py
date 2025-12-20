import cv2
import numpy as np
from pathlib import Path
import math

class WallDetector:
    def __init__(self, image_path):
        """Initialize detector with floor plan image"""
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.lines = None
        self.corners = None
        
        
    def detect_line_segments(self, blur_kernel=5, blur_sigma=1.5, canny_low=30, canny_high=100, 
                            hough_threshold=15, min_line_length=50, max_line_gap=20):
        """
        Detect line segments from black lines on white background
        
        Parameters to tune:
          - blur_kernel: Gaussian blur kernel (5, 7, 9) - larger = smoother
          - blur_sigma: Blur amount (1.0-2.5)
          - canny_low: Lower Canny threshold (20-50) - lower detects more
          - cancy_high: Upper Canny threshold (80-150) - higher detects fewer
          - hough_threshold: Minimum votes (10-30) - LOWER = detect more lines
          - min_line_length: Minimum line length in pixels (30-100)
          - max_line_gap: Gap tolerance to connect segments (10-30)
        """
        # Blur to reduce noise
        blurred = cv2.GaussianBlur(self.gray, (blur_kernel, blur_kernel), blur_sigma)
        
        # Invert: make black lines white for edge detection
        inverted = cv2.bitwise_not(blurred)
        
        # Aggressive erosion to collapse both edges of black line into single centerline
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        eroded = cv2.erode(inverted, kernel, iterations=5)  # Heavy erosion
        
        # Dilate back to restore line visibility
        dilated = cv2.dilate(eroded, kernel, iterations=3)
        
        # Edge detection on processed image
        edges = cv2.Canny(dilated, canny_low, canny_high)
        
        # Dilate slightly to reconnect broken segments
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Hough line detection
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=hough_threshold,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap
        )
        
        if lines is None:
            lines = []
        else:
            lines = [line[0] for line in lines]
        
        self.lines = lines
        print(f"✓ Detected {len(lines)} line segments")
        return lines
    
    def snap_angles(self, angle_threshold=10):
        """Snap line angles to nearest 0° or 90°"""
        if self.lines is None:
            return
        
        snapped = []
        for line in self.lines:
            x1, y1, x2, y2 = line
            
            # Calculate angle
            dx = x2 - x1
            dy = y2 - y1
            angle = math.degrees(math.atan2(dy, dx))
            angle = angle % 180  # Normalize to 0-180
            
            # Snap to 0° or 90°
            if abs(angle) <= angle_threshold or abs(angle - 180) <= angle_threshold:
                # Make horizontal
                new_y1 = (y1 + y2) // 2
                snapped.append([x1, new_y1, x2, new_y1])
            elif abs(angle - 90) <= angle_threshold:
                # Make vertical
                new_x1 = (x1 + x2) // 2
                snapped.append([new_x1, y1, new_x1, y2])
            else:
                snapped.append(line)
        
        self.lines = snapped
        print(f"✓ Angles snapped to 0°/90°")
    
    def find_corners(self, tolerance=30):
        """Find intersections/corners where lines meet"""
        if self.lines is None or len(self.lines) < 2:
            return []
        
        corners = []
        
        for i, line1 in enumerate(self.lines):
            x1, y1, x2, y2 = line1
            
            for j, line2 in enumerate(self.lines):
                if i >= j:
                    continue
                
                x3, y3, x4, y4 = line2
                
                # Find intersection point
                intersection = self.line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                
                if intersection is not None:
                    ix, iy = intersection
                    
                    # Check if intersection is within tolerance of both lines
                    if (self.point_on_line(ix, iy, x1, y1, x2, y2, tolerance) and
                        self.point_on_line(ix, iy, x3, y3, x4, y4, tolerance)):
                        
                        # Calculate angle at corner
                        angle1 = math.degrees(math.atan2(y2 - y1, x2 - x1))
                        angle2 = math.degrees(math.atan2(y4 - y3, x4 - x3))
                        corner_angle = abs(angle2 - angle1)
                        if corner_angle > 90:
                            corner_angle = 180 - corner_angle
                        
                        corners.append((ix, iy, corner_angle))
        
        self.corners = corners
        print(f"✓ Found {len(corners)} corners")
        return corners
    
    def line_intersection(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Find intersection of two lines"""
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        
        return (int(ix), int(iy))
    
    def point_on_line(self, px, py, x1, y1, x2, y2, tolerance):
        """Check if point is on line segment (within tolerance)"""
        dist = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1) / math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
        on_segment = (min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance and
                     min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance)
        return dist <= tolerance and on_segment
    
    def draw_and_save(self, output_path="output_corrected_map.jpg"):
        """Draw lines and corners with angles, save to image"""
        output = self.image.copy()
        
        # Draw lines in red
        for line in self.lines:
            x1, y1, x2, y2 = line
            cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # Draw corners and angles
        if self.corners:
            for ix, iy, angle in self.corners:
                # Draw corner circle
                cv2.circle(output, (ix, iy), 5, (0, 255, 0), -1)
                
                # Write angle text
                angle_text = f"{angle:.1f}°"
                cv2.putText(output, angle_text, (ix + 10, iy - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Save
        cv2.imwrite(output_path, output)
        print(f"✓ Saved to: {output_path}")
        return output_path
    
    def process(self, output_path="output_corrected_map.jpg"):
        """Run pipeline"""
        print(f"\nProcessing: {self.image_path}")
        print("-" * 50)
        
        self.detect_line_segments(
            blur_kernel=5,
            blur_sigma=1.5,
            canny_low=30,
            canny_high=100,
            hough_threshold=15,
            min_line_length=50,
            max_line_gap=20
        )
        
        self.snap_angles(angle_threshold=10)
        self.find_corners(tolerance=30)
        self.draw_and_save(output_path)
        
        print("-" * 50)
        print(f"✓ Done!\n")


def main():
    """Main execution"""
    maps_dir = Path("c:/Users/sidha/Desktop/maps")
    
    # Hardcoded filename
    filename = "first plain.jpg"
    target_image = str(maps_dir / filename)
    
    # Check if file exists
    if not Path(target_image).exists():
        print(f"Error: File not found: {target_image}")
        return
    
    print(f"Using image: {target_image}")
    
    # Run detection pipeline
    detector = WallDetector(target_image)
    detector.process(output_path=str(maps_dir / "output_corrected_map.jpg"))


if __name__ == "__main__":
    if __name__ == "__main__":
        main()
