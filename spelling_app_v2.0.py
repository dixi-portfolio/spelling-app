import json
import os
import platform
import csv
import subprocess
import sys
import base64
import re

# --- Core Functions ---

def speak(text, rate=150):
    """
    Converts text to speech by launching a separate, clean Python process.
    This is a robust method to avoid pyttsx3 driver state issues.
    Uses base64 encoding to safely pass the text.
    Accepts a 'rate' parameter to control speech speed.
    """
    try:
        encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        python_executable = sys.executable
        script = (
            "import pyttsx3, base64; "
            "engine = pyttsx3.init(); "
            f"engine.setProperty('rate', {rate}); "
            f"text_to_speak = base64.b64decode('{encoded_text}').decode('utf-8'); "
            "engine.say(text_to_speak); "
            "engine.runAndWait()"
        )
        command = [python_executable, "-c", script]
        subprocess.run(command, check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("\n[TTS Error] Could not speak. Falling back to text.")
        print(f"Spoken: {text}")
        if isinstance(e, subprocess.CalledProcessError):
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
    """Checks if the TTS engine is working on startup."""
    clear_screen()
    try:
        print("Testing text-to-speech engine...")
        speak("Text to speech engine is ready.")
        print("TTS engine test successful! You should have heard a voice.")
    except Exception:
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
        word_text = input(f"{len(words) + 1}: ").strip()
        if word_text.lower() == 'done':
            if words:
                break
            else:
                print("Please enter at least one word.")
        elif word_text:
            # Store as a dictionary to match the new structure
            words.append({'id': str(len(words) + 1), 'word': word_text})
    return words

def load_from_file():
    """Loads words from a user-specified .txt or .csv file."""
    clear_screen()
    filename_input = input("Enter filename (e.g., words.csv) or path to your file: ").strip()
    filepath = filename_input if os.path.exists(filename_input) else None
    if not filepath:
        print(f"\nError: '{filename_input}' not found.")
        input("Press Enter to continue...")
        return None

    words = []
    try:
        if filepath.lower().endswith('.txt'):
            with open(filepath, 'r') as f:
                for i, line in enumerate(f):
                    if line.strip():
                        words.append({'id': str(i + 1), 'word': line.strip()})
        elif filepath.lower().endswith('.csv'):
            with open(filepath, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header row
                for i, row in enumerate(reader):
                    if row and len(row) >= 2 and row[0].strip() and row[1].strip():
                        words.append({'id': row[0].strip(), 'word': row[1].strip()})
        else:
            print("\nError: Unsupported file type. Please use .txt or .csv.")
            input("Press Enter to continue...")
            return None

        if not words:
            print("\nWarning: The file is empty or contains no valid word entries.")
        else:
            print(f"\nSuccessfully loaded {len(words)} words from '{os.path.basename(filepath)}'.")

    except Exception as e:
        print(f"\nAn error occurred while reading the file: {e}")
        input("Press Enter to continue...")
        return None

    input("Press Enter to continue...")
    return words if words else None

def create_word_list():
    """Lets the user choose how to create a word list."""
    # ... (This function remains the same as before)
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
            return None
        else:
            print("Invalid choice, please try again.")
            input("Press Enter to continue...")


def save_list(words):
    """Saves the current list of words to a JSON file."""
    # ... (This function remains the same as before)
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
    # ... (This function remains the same as before)
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

def select_words_for_test(all_words):
    """Displays the list and lets the user select which words to test."""
    clear_screen()
    print("--- Select Words for the Test ---")
    for item in all_words:
        print(f"  ID {item['id']}: {item['word']}")
    print("-" * 30)
    
    user_input = input("Enter IDs to test (e.g., 1-5, 8, 10-12) or type 'all': ").strip().lower()

    if user_input == 'all':
        return all_words

    selected_ids = set()
    parts = user_input.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                for i in range(start, end + 1):
                    selected_ids.add(str(i))
            except ValueError:
                print(f"Warning: Invalid range '{part}' ignored.")
        else:
            try:
                selected_ids.add(str(int(part)))
            except ValueError:
                 print(f"Warning: Invalid ID '{part}' ignored.")
    
    selected_words = [item for item in all_words if item['id'] in selected_ids]
    return selected_words

def start_spelling_test(words):
    """Starts the interactive dictation test with a practice loop."""
    if not words:
        print("There are no words in the list to start a test.")
        input("Press Enter to continue...")
        return

    words_to_test = select_words_for_test(words)

    if not words_to_test:
        print("\nNo words were selected for the test.")
        input("Press Enter to return to the main menu.")
        return

    while True:
        test_results = []
        for i, item in enumerate(words_to_test):
            word = item['word']
            clear_screen()
            print(f"Word {i + 1} of {len(words_to_test)}")
            print("\nListen carefully...")
            speak(f"The word is {word}", rate=130)
            speak(word, rate=130)
            typed_word = input("\nType the word here: ").strip()
            test_results.append({'correct': item, 'typed': typed_word})

        clear_screen()
        print("=" * 40)
        print("  Test Round Complete! Let's check your work.")
        print("=" * 40)
        misspelled_words = [res for res in test_results if res['correct']['word'].lower() != res['typed'].lower()]

        if not misspelled_words:
            print("\nCongratulations! You got a perfect score!")
            break
        else:
            print("\nHere are the words to practice:")
            max_len = max(len(item['correct']['word']) for item in misspelled_words)
            print(f"\n  {'Correct Word'.ljust(max_len)}   |   You Wrote")
            print(f"  {'-' * max_len}---|-{'-' * 12}")
            for item in misspelled_words:
                print(f"  {item['correct']['word'].ljust(max_len)}   |   {item['typed']}")
            
            practice_again = input("\nWould you like to practice these words again? (y/n): ").strip().lower()
            if practice_again == 'y':
                words_to_test = [item['correct'] for item in misspelled_words]
            else:
                print("\nGreat effort! Keep practicing.")
                break
    
    print("\n")
    input("Press Enter to return to the main menu.")

# --- Main Application Loop ---

def main():
    """The main function to run the application."""
    word_list = []
    while True:
        menu_options = {
            "1": "Create a New Word List",
            "2": "Load a Word List",
            "3": "Save Current List",
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
            # Simplified this menu option text
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
    check_tts_engine()
    main()

