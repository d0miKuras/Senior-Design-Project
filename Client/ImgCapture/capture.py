import time
import cv2
from cv2 import VideoCapture
from deepface.detectors import FaceDetector
import base64
import json
import requests


def send_image(img, num):
    _, encrimg = cv2.imencode(".jpg", img)
    img_str = encrimg.tostring()
    img_byte = base64.b64encode(img_str).decode("utf-8")
    img_json = json.dumps({'image':img_byte, "request_num" : str(num)}).encode("utf-8")
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    # payload = json.dumps({"image": im_b64, "request_num" : request_num})
    response = requests.post(api, data=img_json, headers=headers)
    try:
        data = response.json()
        print(data)
    except requests.exceptions.RequestException:
        print(response.text)

if __name__ == "__main__":
    api = "http://127.0.0.1:5000"
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("Image Capture")
    face_detector = FaceDetector.build_model('ssd')
    freeze = False
    face_detected = False
    face_included_frames = 0 #freeze screen if face detected sequantially 5 frames
    freezed_frame = 0
    frame_threshold = 5
    time_threshold = 2
    tic = time.time()
    request_num = 0
    while True:
        ret, frame = cam.read()
        if not ret:
            print("failed to grab image")
            break
        
        raw_img = frame.copy()
        if freeze == False:
            try:
                faces = FaceDetector.detect_faces(face_detector=face_detector, detector_backend='ssd', img=frame, align=False)
            except:
                faces = []
            if len(faces) == 0:
                face_included_frames = 0
        else:
            faces = []

        detected_faces = []
        face_index = 0
        for face, (x,y,w,h) in faces:
            if w > 130: # discards small faces NOTE: might not actually need it
                face_detected = True
                if face_index == 0:
                    face_included_frames = face_included_frames + 1 # increase frame for a single face
                cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0), 1) # draws rectangle around face
                cv2.putText(frame, str(frame_threshold - face_included_frames), (int(x+w/4),int(y+h/1.5)), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 2)
                detected_face = frame[int(y):int(y+h), int(x):int(x+w)] #crop detected face

                detected_faces.append((x, y, w, h))
                face_index = face_index + 1
        if face_detected == True and face_included_frames == frame_threshold and freeze == False:
            freeze = True
            base_img = raw_img.copy()
            detected_faces_final = detected_faces.copy()
            tic = time.time()
        
        if freeze == True:

            toc = time.time()

            if (toc - tic) < time_threshold:

                if freezed_frame == 0:
                    freeze_img = base_img.copy()
                    for detected_face in detected_faces_final:
                        x = detected_face[0]; y = detected_face[1]
                        w = detected_face[2]; h = detected_face[3]
                        cv2.rectangle(freeze_img, (x,y), (x+w,y+h), (0,0,255), 1)
                        tic = time.time()
                time_left = int(time_threshold - (toc - tic) + 1)
                cv2.rectangle(freeze_img, (10, 10), (90, 50), (255, 0, 0), -10)
                cv2.putText(freeze_img, str(time_left), (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)

                cv2.imshow('img', freeze_img)

                freezed_frame = freezed_frame + 1
            else:
                for detected_face in detected_faces_final:
                        x = detected_face[0]; y = detected_face[1]
                        w = detected_face[2]; h = detected_face[3]
                send_image(freeze_img, request_num)
                request_num = request_num + 1
                face_detected = False
                face_included_frames = 0
                freeze = False
                freezed_frame = 0
        else:
            cv2.imshow('img', frame)

        k = cv2.waitKey(1)
        if k%256 == 27:
            break
    
    cam.release()
    cv2.destroyAllWindows()
