import cv2
import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import RPi.GPIO as GPIO

# Setup PCA9685 and servos
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

pan_servo = servo.Servo(pca.channels[0])
tilt_servo = servo.Servo(pca.channels[1])
fire_servo = servo.Servo(pca.channels[2])

# Setup Gel Blaster control pin (optional if you need it)
gel_blaster_pin = 15  # Adjust pin number according to your setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(gel_blaster_pin, GPIO.OUT)
GPIO.output(gel_blaster_pin, GPIO.LOW)

# Function to move servo to a specific angle with constraints
def move_servo(servo, angle, max_angle):
    if angle < 0:
        angle = 0
    elif angle > max_angle:
        angle = max_angle
    servo.angle = angle

# Function to control gel blaster using a servo
def fire_gel_blaster():
    fire_servo.angle = 90  # Adjust this angle to switch on the gel blaster
    time.sleep(3)          # Fire for 3 seconds
    fire_servo.angle = 0   # Adjust this angle to switch off the gel blaster

# Initialize camera
cap = cv2.VideoCapture(0)

# Max angles for pan and tilt
MAX_PAN_ANGLE = 180
MAX_TILT_ANGLE = 60

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Perform object detection (chest detection for people)
    chest_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')  # Use appropriate cascade
    chests = chest_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # If chests are detected, track the largest one
    if len(chests) > 0:
        largest_chest = max(chests, key=lambda x: x[2] * x[3])  # Find the largest chest
        x, y, w, h = largest_chest

        # Calculate center of the chest
        center_x = x + w // 2
        center_y = y + h // 2

        # Calculate angles for pan and tilt servos
        pan_angle = (center_x / frame.shape[1]) * MAX_PAN_ANGLE
        tilt_angle = (center_y / frame.shape[0]) * MAX_TILT_ANGLE

        # Move servos to track the chest
        move_servo(pan_servo, pan_angle, MAX_PAN_ANGLE)
        move_servo(tilt_servo, tilt_angle, MAX_TILT_ANGLE)

        # Fire gel blaster while tracking
        fire_gel_blaster()

    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()

# Cleanup GPIO
GPIO.cleanup()
