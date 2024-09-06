import cv2
import numpy as np

class VideoStream:
    def __init__(self, overlay_path=None):
        self.stream = cv2.VideoCapture(0)
        self.overlay_path = overlay_path
        self.zoom_factor = 1.0  # Default zoom factor (1.0 means no zoom)

        if self.overlay_path:
            self.overlay = cv2.imread(self.overlay_path, cv2.IMREAD_UNCHANGED)  # Read overlay with alpha channel
            self.overlay = self.resize_overlay(self.overlay, 0.01)  # Resize overlay to 10% of video frame size

    def resize_overlay(self, overlay, scale_factor):
        # Get the dimensions of the overlay image
        overlay_height, overlay_width = overlay.shape[:2]
        
        # Resize overlay image based on scale factor
        new_width = int(overlay_width * scale_factor)
        new_height = int(overlay_height * scale_factor)
        resized_overlay = cv2.resize(overlay, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return resized_overlay

    def set_zoom(self, zoom_factor):
        self.zoom_factor = zoom_factor

    def generate_frames(self):
        while True:
            success, frame = self.stream.read()
            if not success:
                break

            # Apply zoom by cropping and resizing
            if self.zoom_factor > 1.0:
                height, width = frame.shape[:2]
                center_x, center_y = width // 2, height // 2
                zoomed_width = int(width / self.zoom_factor)
                zoomed_height = int(height / self.zoom_factor)
                x1 = max(center_x - zoomed_width // 2, 0)
                y1 = max(center_y - zoomed_height // 2, 0)
                x2 = min(center_x + zoomed_width // 2, width)
                y2 = min(center_y + zoomed_height // 2, height)
                
                frame = frame[y1:y2, x1:x2]
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)

            if self.overlay_path:
                # Place the overlay in the center of the frame
                overlay_resized = self.overlay
                x_offset = (frame.shape[1] - overlay_resized.shape[1]) // 2
                y_offset = (frame.shape[0] - overlay_resized.shape[0]) // 2

                for c in range(0, 3):
                    frame[y_offset:y_offset+overlay_resized.shape[0], x_offset:x_offset+overlay_resized.shape[1], c] = (
                        overlay_resized[:, :, c] * (overlay_resized[:, :, 3] / 255.0) +
                        frame[y_offset:y_offset+overlay_resized.shape[0], x_offset:x_offset+overlay_resized.shape[1], c] * (1.0 - overlay_resized[:, :, 3] / 255.0)
                    )

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def stop(self):
        self.stream.release()
        cv2.destroyAllWindows()