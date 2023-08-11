import re
import os
from urllib.parse import urlparse


def abstract_to_pdf_url(abstract_url):
    """Converts ArXiv abstract URL to PDF URL."""
    return abstract_url.replace("/abs/", "/pdf/") + ".pdf"


def extract_and_save_links_by_domain(file_path, save_dir="data"):
    """
    Extract links from the input file and save them into separate .txt files based on their domain names.

    Parameters:
    - file_path: str, path to the input file containing links.
    - save_dir: str, directory to save the extracted links.

    Returns:
    - None
    """

    # Ensure save directory exists
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Read content from the input file
    with open(file_path, 'r') as file:
        content = file.read()

    # Extract all links using regex
    links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)

    # Dictionary to store links by their domain
    domain_links = {}

    for link in links:
        domain = urlparse(link).netloc.split(".")[-2]  # Extract main part of the domain

        # Convert ArXiv abstract links to PDF links
        if domain == "arxiv" and "/abs/" in link:
            link = abstract_to_pdf_url(link)

        if domain in domain_links:
            domain_links[domain].add(link)
        else:
            domain_links[domain] = {link}

    # Save links into separate .txt files based on domain
    for domain, domain_links_set in domain_links.items():
        with open(os.path.join(save_dir, f"{domain}.txt"), 'w') as file:
            file.write("\n".join(sorted(list(domain_links_set))))  # Convert set back to a list for saving

    print(f"Processed and saved links in '{save_dir}' directory.")

# Example usage:
# extract_and_save_links_by_domain("path_to_your_input_file.txt")