from detector import analyze_audio


result = analyze_audio("sample.mp4")

print("Status:", result["status"])
print("Classification:", result["classification"])
print("Limitations:", result["limitations"])