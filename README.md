# Multithreaded-Web-Crawler
A multithreaded web crawler for NEU Fakebook website

## Overview

I wanted to crawl/scrape the NEU Fakebook website as fast as possible using any tools at my disposal. Depending on the random distribution of the 5 hidden keys, crawling can take between 30 to 90 seconds. It launches 10 worker threads and utilizes basic mutexes in order to be thread safe.

## Requirements

Python 3.6+  
requests

## How to Build

```
make
```

## How to Run

```
usage: webcrawler [-h] username password

Web Crawler for Fakebook.com

positional arguments:
  username    Username for Fakebook.com (ping.d)
  password    Password for Fakebook.com (REDACTED)

options:
  -h, --help  show this help message and exit
```

## Design

- Each worker downloads the next page in the queue. If a secret key is found, add it into the secret key list.
- Each worker checks the page's list of URL's with the "visited" set. If not visited, add those new URL's into the queue.
- Workers both consume URL's from the queue and produce new URL's into the queue.

## Random Notes

- The webcrawler always starts off fast for the first ~4000 URL's. Then searching slows down between 4000-6000 URL's. After 6000 URL's, I estimate only 1 worker is working at a time while 9 workers are sitting idle.
- At the beginning, the queue is saturated with many unvisited URL's, and thus every worker has work to do. As more URL's are visited, the queue becomes starved since there are fewer unvisted URL's being added in.