# Real-time Hand Gesture Controlled Slide Navigation

This project uses a real-time gesture recognition system to control PowerPoint or video playback using your webcam.  
It leverages self trained ML model for gesture classification.

## Setup Instructions

1. Clone the repository and navigate into the project directory.  
2. Create and activate a Python virtual environment (optional):

   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Run the application:

   ```
   python app.py
   ```

## Supported Gestures and Their Actions 

- Thumb Up  
  → Triggers the previous slide key press.

- Thumb Down  
  → Triggers the next slide key press.

- Victory  
  → Sends Esc to exit the presentation.

- Open Palm  
  → Sends F5 to start the slide show from the beginning.

- Closed Fist  
  → Sends B to toggle a black screen (pause / resume).

- Pointing Up  
  → Sends M to mute or un-mute audio.

## Notes

1. You must have a webcam connected.  
2. This script uses pyautogui to simulate key presses; keep PowerPoint in focus for it to work.  
3. Default debounce is set to 1.2 seconds to avoid accidental multiple triggers.
