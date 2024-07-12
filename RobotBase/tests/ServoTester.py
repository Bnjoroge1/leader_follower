import time
import HiwonderSDK.Board as Board

# 1500 represents default PWM pos
servo1 = 1500
servo2 = 1500

def set_servo_positions(servo1, servo2):
    Board.setPWMServoPulse(1, servo1, 1000)
    Board.setPWMServoPulse(2, servo2, 1000)
    print(f"Servo1: {servo1} | Servo2: {servo2}")

def main():
    global servo1, servo2
    print("Servo Tester Program")
    print("Commands:")
    print("'w' - Increase Servo1")
    print("'s' - Decrease Servo1")
    print("'e' - Increase Servo2")
    print("'d' - Decrease Servo2")
    print("'q' - Quit")

    set_servo_positions(servo1, servo2)

    try:
        while True:
            command = input("Enter command: ").strip().lower()
            if command == 'w':
                servo1 += 10
            elif command == 's':
                servo1 -= 10
            elif command == 'e':
                servo2 += 10
            elif command == 'd':
                servo2 -= 10
            elif command == 'q':
                break
            else:
                print("Invalid command")
                continue

            # Ensure the servo values remain within a safe range
            servo1 = max(500, min(2500, servo1))
            servo2 = max(500, min(2500, servo2))

            set_servo_positions(servo1, servo2)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        # Reset servos to initial position before exiting
        set_servo_positions(1500, 1500)
        print("Servos reset to initial position")

if __name__ == "__main__":
    main()
