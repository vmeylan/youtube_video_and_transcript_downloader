import os

from src.constants_and_keywords_to_filter import YOUTUBE_VIDEO_DIRECTORY


def correct_typos_in_files(log=True):

    """
    Correct specific typos in .txt files under a given directory.

    Args:
    - root_dir (str): Path to the root directory where search begins.
    """
    # TODO 2024-04-07: parametrise this
    root_dir = YOUTUBE_VIDEO_DIRECTORY

    # Dictionary of typos and their corrections
    typo_dict = {
        "L Two": "L2",
        "L Two s": "L2s",
        "L Three": "L3s",
        "SWAV": "SUAVE",
        "MVV": "MEV",
        "layer two": "L2",
        "L one": "L1",
    }

    # Walk through root_dir
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith("_diarized_content_processed_diarized.txt"):
                file_path = os.path.join(dirpath, fname)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    for typo, correction in typo_dict.items():
                        content = content.replace(typo, correction)
                        if log:
                            print("Corrected typo: ", typo, " -> ", correction, " in ", file_path, "\n")

                # Write corrected content back to file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)


if __name__ == "__main__":
    correct_typos_in_files()

