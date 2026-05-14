# HIT137_Assignment3_Group
HIT137 Group Assignment 3: A Python-based desktop application demonstrating Object-Oriented Programming, GUI development with Tkinter, and image processing with OpenCV



## Overview
This game displays two side-by-side images — the original and a modified copy. The modified image contains exactly 5 hidden differences generated programmatically using OpenCV. The player clicks on the modified image to locate all the differences before making 3 mistakes.

## Features
- Loads any JPG, PNG, or BMP image from disk
- Automatically generates 5 random, non-overlapping differences
- 5 types of alterations: colour shift, blur, brightness, noise, channel swap
- Red circle marks correctly found differences on both images
- Blue circle reveals unfound differences when "Reveal All" is pressed
- Tracks mistakes (max 3) and total score across multiple images
- Clean dark-themed Tkinter GUI

  ## Python Library
- Tkinter (GUI)
- OpenCV (image processing)
- Pillow (image display)
- NumPy (array operations)

 ## How to run
Install dependencies (once):

pip install opencv-python pillow

## Run the Application

1. Extract the ZIP file to a folder on your computer (e.g. Desktop)
2. In Command Prompt, navigate to that folder by typing:
cd C:\Users\YourName\Desktop\folder-name
3. Press Enter
4. Then type the following and press Enter:
python spot_the_difference.py

5. A game window will open automatically on your screen.



## Click Load Image and pick any `.jpg`, `.png`, or `.bmp` file.

## How to play

Once the game window opens:
1. Click **"📂 Load Image"** button
2. A file browser will pop up — browse and select any image
   from your computer (JPG, JPEG, PNG, or BMP format)
3. Two images will appear side by side:
   - **Left image** → Original (for reference only, cannot be clicked)
   - **Right image** → Modified (click here to find differences)
4. Click on areas in the Modified image where you spot a difference
   - ✅ Correct click → A **red circle** appears on both images
   - ❌ Wrong click → Counts as a **mistake**
5. You are allowed a maximum of **3 mistakes** per image
6. Find all **5 differences** before making 3 mistakes to win!
7. Click **"👁 Reveal All"** to show any remaining differences in blue
8. Load a new image anytime to play again

   
## Project structure

spot\_the\_difference.py   ← single-file application (all 4 classes)
README.md
github\_link.txt


## OOP design
Class         	        Responsibility
`Difference`	          Data model for one hidden region; tracks position, type, and found-state
`ImageProcessor`	      OpenCV image loading and patch alteration (5 types)
`GameState`	            Mistake counting, score tracking, lock-out logic
`SpotTheDifferenceApp`	Tkinter GUI; inherits from `tk.Tk`

## OOP principles used
Encapsulation – each class owns its own data and exposes a clean interface.
Constructor (`\_\_init\_\_`) – every class initialises its own state.
Methods – behaviour is modelled as instance methods, not loose functions.
Inheritance – `SpotTheDifferenceApp` extends `tk.Tk`.
Polymorphism – `\_apply\_alteration` dispatches to different alteration branches via a string tag, behaving differently for the same method call depending on `diff\_type`.
Class interaction – `SpotTheDifferenceApp` owns and delegates to both `ImageProcessor` and `GameState`.

## Image alteration types (OpenCV)
colour_shift – shifts the hue and saturation channels in HSV space.
blur – applies a large-kernel Gaussian blur to the patch.
brightness – adds or subtracts a fixed value across all channels.
noise – scatter random black/white pixels (salt-and-pepper).
swap_channels – exchanges the R and B channels inside the patch.
All alterations are deliberately subtle enough to require careful inspection.
