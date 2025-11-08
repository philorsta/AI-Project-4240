# deepface_demo.py
# Basic DeepFace emotion recognition example

from deepface import DeepFace

# Path to a test image (replace with your own)
img_path = "test_face.jpg"

# Analyze the image
# 'actions' tells DeepFace which attributes to estimate
result = DeepFace.analyze(
    img_path=img_path,
    actions=["emotion", "age", "gender", "race"],
    enforce_detection=False  # prevents crashes if the face isn't detected perfectly
)

# Print results
print("Analysis Results:")
print(f"Emotion: {result[0]['dominant_emotion']}")
print(f"Age: {result[0]['age']}")
print(f"Gender: {result[0]['gender']}")
print(f"Race: {result[0]['dominant_race']}")
