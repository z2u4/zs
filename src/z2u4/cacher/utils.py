import re


def extract_githuburl_params(url: str) -> dict:
    pattern = r"https://github\.com/([^/]+)/([^/]+)(?:/blob/([^/]+))?/?(.+)"
    match = re.match(pattern, url)
    if match:
        return {
            "owner": match.groups()[0],
            "repo": match.groups()[1],
            "branch": match.groups()[2],
            "path": match.groups()[3],
        }
    else:
        raise ValueError("Invalid GitHub URL format.")


def convert_url_to_raw(url: str) -> str:
    """
    Converts a GitHub URL to its raw content URL.

    Args:
        url (str): The GitHub URL to convert.

    Returns:
        str: The raw content URL corresponding to the input GitHub URL.
    """
    params = extract_githuburl_params(url)
    raw_url = f"https://raw.githubusercontent.com/{params['owner']}/{params['repo']}/{params['branch']}/{params['path']}"
    return raw_url, params


def extract_raw_params(url: str) -> dict:
    pattern = r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)"
    match = re.match(pattern, url)
    if match:
        return {
            "owner": match.groups()[0],
            "repo": match.groups()[1],
            "branch": match.groups()[2],
            "path": match.groups()[3],
        }
    else:
        raise ValueError("Invalid GitHub URL format.")


def extract_githubrelease_params(url: str) -> dict:
    pattern = r"https://github\.com/([^/]+)/([^/]+)/releases/tag/([^/]+)"
    pattern2 = r"https://github\.com/([^/]+)/([^/]+)/releases/latest"
    match = re.match(pattern, url)

    if match:
        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "releaseTag": match.group(3),
        }
    else:
        match2 = re.match(pattern2, url)
        if match2:
            return {
                "owner": match2.group(1),
                "repo": match2.group(2),
                "releaseTag": "latest",
            }
        else:
            raise ValueError("Invalid GitHub URL format.")


def convert_githubrelease_to_latest(url: str) -> str:
    params = extract_githubrelease_params(url)
    return f"https://github.com/{params['owner']}/{params['repo']}/releases/latest"
