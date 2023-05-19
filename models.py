import cv2

#================================================================================================
#initializing some variables and constants
FPS = 30
WIDTH = 1280
HEIGHT = 720

FONT = cv2.FONT_HERSHEY_SIMPLEX
stickColor = (0,255,0)
FONT_COLOR = (255,0,255)

stickWidth = 130
stickHeight = 30

#================================================================================================
# My capera object and its settings 
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,HEIGHT)
cap.set(cv2.CAP_PROP_FPS,FPS)
cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))


#================================================================================================
class myHands:
    import mediapipe as mp
    def __init__(self,static_image_mode=False, max_num_hands=2, model_complexity=1,min_detection_confidence=0.5,min_tracking_confidence=0.5):
        self.static_image_mode=static_image_mode
        self.max_num_hands=max_num_hands
        self.model_complexity=model_complexity
        self.min_detection_confidence=min_detection_confidence
        self.min_tracking_confidence=min_tracking_confidence
        self.hands = self.mp.solutions.hands.Hands(self.static_image_mode,self.max_num_hands,self.model_complexity,self.min_detection_confidence,self.min_tracking_confidence)
        self.mpDraw = self.mp.solutions.drawing_utils


    def Marks(self,frame):
        myHands = list() # [[first_hand], [second_hand],[third_hand],[...],...]
        result = self.hands.process(frame)
        if (result.multi_hand_landmarks is not None):
            for hand in result.multi_hand_landmarks:
                myHand = list()
                for handLandMarks in hand.landmark:
                    myHand.append((int(handLandMarks.x * WIDTH),int(handLandMarks.y * HEIGHT)))
                myHands.append(myHand)
        return [myHands,result]


    def drawConnection(self,rgbFrame,bgrFrame):
        result = self.Marks(rgbFrame)[1]
        if result.multi_hand_landmarks is not None:
            for LandMarks in result.multi_hand_landmarks:
                    self.mpDraw.draw_landmarks(bgrFrame,LandMarks,self.mp.solutions.hands.HAND_CONNECTIONS)


#================================================================================================
mpHands = myHands()
class main():
    def main():
        while True:
            isTrue,frame = cap.read()

            if not(isTrue):
                break
            frame = cv2.flip(frame,1)
            rgbFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            myHands = mpHands.Marks(rgbFrame)

            if len(myHands[0]) >= 1:
                for hand in myHands[0]:
                    cv2.rectangle(
                        frame,
                        (int(hand[8][0] - stickWidth/2),0), 
                        (int(hand[8][0] + stickWidth/2), stickHeight),
                        (0,255,0),
                        -1
                    )
                    
        cap.release()   


        return

