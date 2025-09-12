import json
import os
import platform
import csv
import subprocess
import sys
import base64

# --- Core Functions ---

def speak(text, rate=150):
    """
    Converts text to speech by launching a separate, clean Python process.
    This is a robust method to avoid pyttsx3 driver state issues.
    Uses base64 encoding to safely pass the text.
    Accepts a 'rate' parameter to control speech speed.
    """
    try:
        # Encode text to base64 to avoid any shell quoting issues with special characters.
        encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
        # Get the path to the current python executable to ensure we use the same one.
        python_executable = sys.executable
        
        # This is a mini-Python script that will be run in a separate process.
        # It decodes the text, sets the speech rate, and speaks.
        script = (
            "import pyttsx3, base64; "
            "engine = pyttsx3.init(); "
            f"engine.setProperty('rate', {rate}); "
            f"text_to_speak = base64.b64decode('{encoded_text}').decode('utf-8'); "
            "engine.say(text_to_speak); "
            "engine.runAndWait()"
        )
        
        command = [python_executable, "-c", script]
        
        # Execute the command silently.
        subprocess.run(command, check=True, capture_output=True)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("\n[TTS Error] Could not speak. Falling back to text.")
        print(f"Spoken: {text}") # Fallback behavior
        if isinstance(e, subprocess.CalledProcessError):
             # This provides debug info if the subprocess fails for some reason.
             print(f"[DEBUG] Subprocess error: {e.stderr.decode()}")


def clear_screen():
    """Clears the terminal screen for a cleaner interface."""
    command = 'cls' if platform.system().lower() == 'windows' else 'clear'
    os.system(command)

def display_menu(title, options):
    """Displays a formatted menu."""
    clear_screen()
    print("=" * 30)
    print(f"  {title}")
    print("=" * 30)
    for key, value in options.items():
        print(f"  {key}. {value}")
    print("-" * 30)
    return input("Choose an option: ")

# --- TTS Engine Check ---

def check_tts_engine():
    """Checks if the TTS engine is working on startup using the new speak method."""
    clear_screen()
    try:
        print("Testing text-to-speech engine...")
        speak("Text to speech engine is ready.")
        print("TTS engine test successful! You should have heard a voice.")
    except Exception:
        # The speak function now handles its own errors, but this is a safeguard.
        print(f"\n--- TTS ENGINE ALERT ---")
        print(f"The text-to-speech engine failed during test.")
        print("The app will print words to the screen instead of speaking them.")
        print("--------------------------\n")
    
    input("Press Enter to continue to the main menu...")


# --- Word List Management ---

def create_word_list_manually():
    """Allows the user to create a new list of spelling words by typing them."""
    clear_screen()
    print("Enter your spelling words. Type 'done' when you are finished.\n")
    words = []
    while True:
        word = input(f"{len(words) + 1}: ").strip()
        if word.lower() == 'done':
            if words:
                break
            else:
                print("Please enter at least one word.")
        elif word:
            words.append(word)
    return words

def load_from_file():
    """Loads words from a user-specified .txt or .csv file."""
    clear_screen()
    filename = input("Enter the path to your .txt or .csv file: ").strip()

    if not os.path.exists(filename):
        print("\nError: File not found.")
        input("Press Enter to continue...")
        return None

    words = []
    try:
        if filename.lower().endswith('.txt'):
            with open(filename, 'r') as f:
                words = [line.strip() for line in f if line.strip()]
        elif filename.lower().endswith('.csv'):
            with open(filename, 'r', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    words.extend([word.strip() for word in row if word.strip()])
        else:
            print("\nError: Unsupported file type. Please use .txt or .csv.")
            input("Press Enter to continue...")
            return None

        if not words:
            print("\nWarning: The file is empty or contains no words.")
        else:
            print(f"\nSuccessfully loaded {len(words)} words from '{filename}'.")

    except Exception as e:
        print(f"\nAn error occurred while reading the file: {e}")
        input("Press Enter to continue...")
        return None

    input("Press Enter to continue...")
    return words if words else None

def create_word_list():
    """Lets the user choose how to create a word list."""
    menu_options = {
        "1": "Enter words manually",
        "2": "Load from a file (.txt or .csv)",
        "3": "Back to Main Menu"
    }
    while True:
        choice = display_menu("Create Word List", menu_options)
        if choice == '1':
            return create_word_list_manually()
        elif choice == '2':
            words = load_from_file()
            if words:
                return words
        elif choice == '3':
            return None  # No new list was created
        else:
            print("Invalid choice, please try again.")
            input("Press Enter to continue...")

def save_list(words):
    """Saves the current list of words to a JSON file."""
    if not words:
        print("No words to save.")
        input("Press Enter to continue...")
        return

    clear_screen()
    filename = input("Enter a filename to save the list (e.g., week1.json): ").strip()
    if not filename.endswith('.json'):
        filename += '.json'

    try:
        with open(filename, 'w') as f:
            json.dump(words, f, indent=4)
        print(f"\nList successfully saved as '{filename}'")
    except IOError as e:
        print(f"\nError: Could not save file. {e}")
    input("Press Enter to continue...")

def load_list():
    """Loads a list of words from a JSON file."""
    clear_screen()
    files = [f for f in os.listdir() if f.endswith('.json')]
    if not files:
        print("No saved word lists found (.json files).")
        input("Press Enter to continue...")
        return None

    print("Available word lists:")
    for i, filename in enumerate(files, 1):
        print(f"  {i}. {filename}")
    print("-" * 30)

    try:
        choice = int(input("Which list would you like to load? "))
        if 1 <= choice <= len(files):
            filename = files[choice - 1]
            with open(filename, 'r') as f:
                words = json.load(f)
            print(f"\nSuccessfully loaded '{filename}'.")
            input("Press Enter to continue...")
            return words
        else:
            print("Invalid choice.")
    except (ValueError, IndexError):
        print("Invalid input. Please enter a number from the list.")
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading file: {e}")

    input("Press Enter to return to the main menu...")
    return None


# --- Spelling Test ---

def start_spelling_test(words):
    """Starts the interactive dictation test."""
    if not words:
        print("There are no words in the list to start a test.")
        input("Press Enter to continue...")
        return

    test_results = []
    for i, word in enumerate(words):
        clear_screen()
        print(f"Word {i + 1} of {len(words)}")
        print("\nListen carefully...")

        # Speak the intro phrase, then pause and speak the word slower, twice.
        speak("The word is")
        speak(word, rate=130) # Slower rate for the actual word.
        speak(word, rate=130) # Speak it a second time.
        
        # Get the child's input
        typed_word = input("\nType the word here: ").strip()
        
        # Store the result
        test_results.append({'correct': word, 'typed': typed_word})

    # --- Review Screen ---
    clear_screen()
    print("=" * 40)
    print("  Test Complete! Let's check your work.")
    print("=" * 40)

    misspelled_words = []
    for result in test_results:
        if result['correct'].lower() != result['typed'].lower():
            misspelled_words.append(result)

    if not misspelled_words:
        print("\nCongratulations! You got a perfect score!")
        print("You spelled every word correctly. Great job!")
    else:
        print("\nHere are the words to practice:")
        # Find the longest correct word for formatting
        max_len = max(len(item['correct']) for item in misspelled_words)
        
        print(f"\n  {'Correct Word'.ljust(max_len)}   |   You Wrote")
        print(f"  {'-' * max_len}---|-{'-' * 12}")
        
        for item in misspelled_words:
            print(f"  {item['correct'].ljust(max_len)}   |   {item['typed']}")

    print("\n")
    input("Press Enter to return to the main menu.")


# --- Main Application Loop ---

def main():
    """The main function to run the application."""
    word_list = []
    while True:
        menu_options = {
            "1": "Create a New Word List",
            "2": "Load a Word List (.json)",
            "3": "Save Current List (.json)",
            "4": "Start Spelling Test",
            "5": "Exit"
        }
        if not word_list:
            menu_options["3"] = "Save Current List (No list loaded)"
            menu_options["4"] = "Start Spelling Test (No list loaded)"

        choice = display_menu("Spelling App", menu_options)

        if choice == '1':
            new_list = create_word_list()
            if new_list is not None:
                word_list = new_list
        elif choice == '2':
            loaded_words = load_list()
            if loaded_words:
                word_list = loaded_words
        elif choice == '3':
            save_list(word_list)
        elif choice == '4':
            start_spelling_test(word_list)
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    # The initial check now uses the same robust speak function.
    check_tts_engine()
    main()

