"""
Course Web Crawler

Gabriela Ayala
"""
# DO NOT REMOVE THESE LINES OF CODE
# pylint: disable-msg=invalid-name, redefined-outer-name, unused-argument, unused-variable

import queue
import json
import sys
import csv
import re
from this import d
import bs4
import util
import requests


INDEX_IGNORE = set(['a', 'also', 'an', 'and', 'are', 'as', 'at', 'be',
                    'but', 'by', 'course', 'for', 'from', 'how', 'i',
                    'ii', 'iii', 'in', 'include', 'is', 'not', 'of',
                    'on', 'or', 's', 'sequence', 'so', 'social', 'students',
                    'such', 'that', 'the', 'their', 'this', 'through', 'to',
                    'topics', 'units', 'we', 'were', 'which', 'will', 'with',
                    'yet'])


def crawl(num_pages_to_crawl):
    '''
    Crawls links on a page from a starting url and generates an index
    of words and course codes.
    Inputs:
        starting url
        n (int) : max number of pages to visit
    Output: 
        (dict): dictionary of words mapped to course codes
    '''
    starting_url = ("http://www.classes.cs.uchicago.edu/archive/2015/winter"
                    "/12200-1/new.collegecatalog.uchicago.edu/index.html")
    limiting_domain = "classes.cs.uchicago.edu"

    q = queue.Queue() 
    q.put(starting_url)
    num_page_visited = 0
    urls_visited = set()
    q_tracker = set()
    index = {}

    while num_page_visited <= num_pages_to_crawl or q.empty():
        url = q.get()
   
        if make_soup(url, limiting_domain) is not None:
            true_url, soup = make_soup(url, limiting_domain)
        else:
            url = q.get()
     
        links = soup.find_all("a")
        urls_visited.add(true_url)

        for i in links:
            if i.has_attr("href"):
                new_url = util.remove_fragment(i.attrs["href"])
                if not util.is_absolute_url(new_url):
                    new_url = util.convert_if_relative_url(url, new_url) 
            if util.is_url_ok_to_follow(new_url, limiting_domain) and \
                new_url not in urls_visited:
                if new_url not in q_tracker:
                    q_tracker.add(new_url)
                    q.put(new_url)
        
        temp = temp_index(soup) # Dictionary mapping words to course codes
        index.update(temp)
        num_page_visited += 1
       
    return index


def make_soup(url, limiting_domain):
    '''
    Checks if a given URL is valid and creates soup object.
    Inputs:
        (str) a URL
        (str) limiting domain
    Output:
        (tuple) true URL and soup object if URL passed in is 
        valid, NoneType otherwise.
    '''
    if util.is_url_ok_to_follow(url, limiting_domain):
        if util.get_request(url) is not None:
            request = util.get_request(url)
            true_url = util.get_request_url(request)
            if util.read_request(request) != "":
                s = util.read_request(request)
                soup = bs4.BeautifulSoup(s, "html5lib")
                return true_url, soup
            else:
                return None
        else:
            return None
    else:
        return None


def process_word(string):
    '''
    Proccesses a word.
    Input: (str) the word
    Output: (str) processed words
    '''

    if len(string) >= 1:
        w = string.lower()
        if w.endswith(("!", ".", ":")):
            word = w[-1]
        else:
            word = w
        if word not in INDEX_IGNORE:
            return word
          

def temp_index(soup):
    '''
    Maps words to a list of course codes where they appear in the 
    course catalog.
    Input: 
        (soup) soup object
    Output: 
        (dict) dictionary mapping words to list of course codes.
    '''
    index = {}
    divs = soup.find_all("div", class_ = 'courseblock main')

    for div in divs:
        main_words = []
        #Create set of words in Main Course Title and Description
        main_title = div.find("p", class_ = 'courseblocktitle').text
        course_code = (str(main_title.strip()[0:10])).replace(u'\xa0', u' ') #Main Course Code
        main_title_text = main_title.strip()[10:].split() #Ignore Course Code from title text
        for w in main_title_text:
            word = process_word(w) 
            main_words.append(word)
        
        main_desc = div.find("p", class_ = 'courseblockdesc').text.lower()
        main_desc = main_desc.strip().split()
        for w in main_desc:
            word = process_word(w)
            main_words.append(word)
        #Dictionary mapping words to course code
        for word in main_words:
            index[word] = [course_code]
        
        #Create set of words in Sequence Course Title 
        sequences = util.find_sequence(div) 
        if sequences != []: 
            for div in sequences:
                seq_words = []
                seq_title = div.find("p", class_ = 'courseblocktitle').text
                seq_code = (str(seq_title.strip()[0:10])).replace(u'\xa0', u' ')
                seq_title_text = seq_title.strip()[10:].split()
                for w in seq_title_text:
                    word = process_word(w) 
                    seq_words.append(word)
                #Updating dictionary with sequence words and code
                for word in seq_words:
                    if word not in index:
                        index[word] = [seq_code]
                    else:
                        index[word].append(seq_code)

    return index 

def go(num_pages_to_crawl, course_map_filename, index_filename):
    '''
    Crawl the college catalog and generates a CSV file with an index.

    Inputs:
        num_pages_to_crawl: the number of pages to process during the crawl
        course_map_filename: the name of a JSON file that contains the mapping
          course codes to course identifiers
        index_filename: the name for the CSV of the index.

    Outputs:
        CSV file of the index index.
    '''

    with open(course_map_filename) as fp:
        data = json.load(fp)
        
    temp_index = crawl(num_pages_to_crawl)
    final_index = {}

    for word, course_lst in temp_index.items():
        for course_code in course_lst:
            identifier = data[course_code]
            final_index[identifier] = word
    
    with open(index_filename, "w") as csvfile:
        spamwriter = csv.writer(csvfile, delimiter="|")
        for code, word in final_index.items():
            spamwriter.writerow([code, word])

####

if __name__ == "__main__":
    usage = "python3 crawl.py <number of pages to crawl>"
    args_len = len(sys.argv)
    course_map_filename = "course_map.json"
    index_filename = "catalog_index.csv"
    if args_len == 1:
        num_pages_to_crawl = 1000
    elif args_len == 2:
        try:
            num_pages_to_crawl = int(sys.argv[1])
        except ValueError:
            print(usage)
            sys.exit(0)
    else:
        print(usage)
        sys.exit(0)

    go(num_pages_to_crawl, course_map_filename, index_filename)

