import argparse
import queue
import requests
import re
import time
import threading
import concurrent.futures as futures

# Global data structures should be thread locked when modifying them
FOUND = set()
FRONTIER = queue.Queue()
SECRET_FLAGS = []

lock = threading.Lock()

# Regex pattern tools
csrf_regex = re.compile(r'name="csrfmiddlewaretoken" value="(.*?)"')
anchor_regex = re.compile(r'<a href="(/fakebook/.*?)"')
secret_flag_regex = re.compile(r'<h2 class=\'secret_flag\' style="color:red">FLAG: (.*?)</h2>')


def newSession(csrftoken: str, sessionid: str) -> requests.Session:
    """
    Create and return a new HTTP session with the given csrftoken and sessionid.
    """
    session = requests.Session()
    session.headers.update({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Host": "project2.5700.network",
        "Connection": "keep-alive",
        "Cookie": "csrftoken={}; sessionid={}".format(csrftoken, sessionid),
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"
    })
    return session


def parsePage(body: str) -> None:
    """
    Parse an HTML page, add all new links to the frontier, and check for secret flags.
    """
    anchors = anchor_regex.findall(body)
    secret_flag = secret_flag_regex.findall(body)
    if secret_flag:
        print(f"Found secret flag: {secret_flag[0]}")
        with lock:
            SECRET_FLAGS.append(secret_flag[0])
    for anchor in anchors:
        url = "https://project2.5700.network" + anchor
        if url not in FOUND:
            with lock:
                FOUND.add(url)
                FRONTIER.put(url)
    return


def downloadPage(session: requests.Session) -> None:
    """
    Use an HTTP session to download the next url in the queue.
    If status code = 200, call parsePage().
    """
    if not FRONTIER.empty():
        with lock:
            next_url = FRONTIER.get()
        response = session.get(next_url, timeout=5)
        if response.status_code == 200:
            parsePage(response.text)
            return
        elif response.status_code == 403 or response.status_code == 404:
            return
        elif response.status_code == 500 or response.status_code == 503:
            retry = session.get(response.url, timeout = 5)
            while retry.status_code != 200:
                retry = session.get(response.url, timeout = 5)
            parsePage(retry.text)
            return
        else:
            print(f"Unknown status code: {response.status_code}")
            return


def multithreadedSearch(csrftoken: str, sessionid: str) -> None:
    """
    Init 10 threads to download and search pages concurrently.
    """
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        session = newSession(csrftoken, sessionid)
        while len(SECRET_FLAGS) < 5:
            done, notDone = futures.wait(
                [executor.submit(downloadPage, session) for _ in range(10)],
                return_when=futures.FIRST_COMPLETED
            )
            for future in done:
                future.result()
            for future in notDone:
                future.cancel()
        session.close()
            

def main() -> None:
    parser = argparse.ArgumentParser(prog="webcrawler",
                                    description='Web Crawler for Fakebook.com',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("username", type=str, help="Username for Fakebook.com (ping.d)")
    parser.add_argument("password", type=str, help="Password for Fakebook.com (REDACTED)")
    args = parser.parse_args()
    username: str = args.username
    password: str = args.password

    start = time.time()
    session = requests.Session()

    # Login process
    login_page = "https://project2.5700.network/accounts/login/"
    res = session.get(login_page)
    csrfmiddleware = csrf_regex.findall(res.text)[0]
    post_data = {
        "username": username,
        "password": password,
        "csrfmiddlewaretoken": csrfmiddleware,
        "next": "/fakebook/"
    }
    res = session.post(login_page, post_data)
    destination = res.url
    try:
        res = session.get(destination)
    except:
        print(f"LOGIN FAILED: {destination}")
        session.close()
        return
    else:
        print(f"LOGIN SUCCESS: {destination}")
        FOUND.add(destination)
        FRONTIER.put(destination)
        
    # Extract the csrf and sessionid for the multithreaded sessions
    csrftoken = session.cookies.get("csrftoken")
    sessionid = session.cookies.get("sessionid")
    session.close()

    parsePage(res.text) # Seed the frontier with the initial page

    multithreadedSearch(csrftoken, sessionid) # Go baby go!

    end = time.time()
    print(f"Found 5 flags in {str(round(end - start, 3))} seconds")
    print(f"Collected {str(len(SECRET_FLAGS))} secret flags")


if __name__ == "__main__":
    main()