import re
import os
from urllib.parse import urlparse


def abstract_to_pdf_url(abstract_url):
    """Converts ArXiv abstract URL to PDF URL."""
    return abstract_url.replace("/abs/", "/pdf/") + ".pdf"


def save_links_by_category(links, research_list, save_dir="links"):
    """
    Save links based on the specified categories.

    Parameters:
    - links: list, all the links extracted from the input file.

    Returns:
    - None
    """

    categorized_links = {
        "arxiv.txt": [],
        "youtube.txt": [],
        "twitter.txt": [],
        "research.txt": [],
        "other_links.txt": []
    }

    for link in links:
        domain = urlparse(link).netloc

        if "arxiv.org" in domain and ("/abs/" in link or "/pdf/" in link):
            link = link if "/pdf/" in link else abstract_to_pdf_url(link)
            if link not in categorized_links["arxiv.txt"]:
                categorized_links["arxiv.txt"].append(link)
        elif "youtube.com" in domain or "youtu.be" in domain:
            if link not in categorized_links["youtube.txt"]:
                categorized_links["youtube.txt"].append(link)
        elif "twitter.com" in domain:
            if link not in categorized_links["twitter.txt"]:
                categorized_links["twitter.txt"].append(link)
        elif any(sub in link for sub in research_list):
            if link not in categorized_links["research.txt"]:
                categorized_links["research.txt"].append(link)
        else:
            if link not in categorized_links["other_links.txt"]:
                categorized_links["other_links.txt"].append(link)

    # Saving to files
    for filename, links_list in categorized_links.items():
        with open(os.path.join(save_dir, filename), 'w') as file:
            file.write("\n".join(links_list))

    print(f"Processed and saved links in '{save_dir}' directory.")



def extract_and_save_links_by_category(file_path, save_dir="links"):
    """
    Extract links from the input file and save them based on the defined categories.

    Parameters:
    - file_path: str, path to the input file containing links.
    - save_dir: str, directory to save the extracted links.

    Returns:
    - None
    """

    # Ensure save directory exists
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    with open(file_path, 'r') as file:
        content = file.read()

    links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)

    save_links_by_category(links, save_dir)


def process_and_save_links(input_file_path, save_dir="data/links"):
    """
    The main function to process links and save them according to the defined categories.

    Parameters:
    - input_file_path: str, path to the input file containing links.
    - save_dir: str, directory to save the extracted links.

    Returns:
    - None
    """
    extract_and_save_links_by_category(input_file_path, save_dir)