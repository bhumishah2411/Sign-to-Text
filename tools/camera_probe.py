import cv2

print('Camera probe starting...')
for i in range(0, 7):
    try:
        cap = cv2.VideoCapture(i)
        opened = cap.isOpened()
        print(f'Index {i}: opened={opened}')
        if opened:
            ret, frame = cap.read()
            print(f'  read={ret}, shape={None if frame is None else frame.shape}')
            cap.release()
    except Exception as e:
        print(f'  Exception for index {i}: {e}')
print('Camera probe complete.')
