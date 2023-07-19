'''
Linking restaurant records in Zagat and Fodor's list using restraurant
names, cities, and street addresses.

Maria Gabriela Ayala
'''
import csv
import itertools
import jellyfish
import pandas as pd
import util

ZAGAT_FILE = "data/zagat.csv"
FODORS_FILE = "data/fodors.csv"
KNOWN_LINKS_FILE = "data/known_links.csv"
UNMATCHED_FILE = "data/unmatch_pairs.csv"


def find_matches(output_filename, mu, lambda_, block_on_city=False):
  '''
  Put it all together: read the data and apply the record linkage
  algorithm to classify the potential matches.
  Inputs:
    output_filename (string): the name of the output file,
    mu (float) : the maximum false positive rate,
    lambda_ (float): the maximum false negative rate,
    block_on_city (boolean): indicates whether to block on the city or not.
  '''
  zagat = (pd.read_csv(ZAGAT_FILE)).rename(columns={'street address':\
    'address', 'restaurant name': 'name'})
  fodors = (pd.read_csv(FODORS_FILE)).rename(columns={'street address':\
    'address', 'restaurant name': 'name'})
  categorize = classifier(UNMATCHED_FILE, KNOWN_LINKS_FILE, mu, lambda_)
  
  with open(output_filename, "w") as csvfile:
    record_linkage = csv.writer(csvfile, delimiter = ",")
    if not block_on_city:
      for z_idx, z_row in zagat.iterrows():
        for f_idx, f_row in fodors.iterrows():
          sim_tuple = get_prob_blocks(z_row, f_row)
          label = categorize[sim_tuple]
          record_linkage.writerow([z_idx, f_idx,label])         
    else:
      for z_idx, z_row  in zagat.iterrows():
        for f_idx, f_row in fodors.iterrows():
          if z_row["city"] == f_row["city"]:
            sim_tuple = get_prob_blocks(z_row, f_row)
            label = categorize[sim_tuple]
            record_linkage.writerow([z_idx, f_idx,label])


def get_prob_blocks(z_row, f_row):
  '''
  Computes Jaro-Winkler score for three fields (restaurant name,
  city and address) between two data entries. Converts similarity 
  score to probability blocks "low" or "medium" or "high".
  Inputs:
    (pd Series): row in Zagat DataFrame
    (pd Series): row in Fodors DataFrame
  Output:
    (tuple): contains probability categorization for each of the three
    fields (cat_restaurant, cat_city, cat_loc)
  '''
  
  jw_rest = jellyfish.jaro_winkler_similarity(z_row["name"], f_row["name"])
  jw_city = jellyfish.jaro_winkler_similarity(z_row["city"], f_row["city"])
  jw_loc = jellyfish.jaro_winkler_similarity(z_row["address"], f_row["address"])             
  cat_rest = util.get_jw_category(jw_rest)
  cat_city = util.get_jw_category(jw_city)
  cat_loc = util.get_jw_category(jw_loc)

  return (cat_rest, cat_city, cat_loc)


def get_sim_tuples(filename):
    '''
    Computes all similarity tuples for a given training data file.
    Input:
        (str): csv training file name (known or unmatched)
    Output:
        (lst): list of similarity tuples
    '''
    file = pd.read_csv(filename)
    zagat = (pd.read_csv(ZAGAT_FILE)).rename(columns={'street address':\
      'address', 'restaurant name': 'name'})
    fodors = (pd.read_csv(FODORS_FILE)).rename(columns={'street address':\
      'address', 'restaurant name': 'name'})

    rv = []

    for _, row in file.iterrows():
        z_row = zagat.iloc[row.zindex]
        f_row = fodors.iloc[row.findex]
        sim_tups = get_prob_blocks(z_row, f_row)
        rv.append(sim_tups)
    
    return rv


def combination(lst):
  '''
  Computes the Cartesian product of a list of variables.
  Input:
    (lst): list containing the variables
  Ouput
    (lst): list of all possible permutations with repetition.
  '''
  rv = []
  n = len(lst)
  
  for comb in itertools.product(lst, repeat = n):
    rv.append(comb)
  
  return rv


def est_prob(filename):
  '''
  Calculates the probabilities of similarity tuples for one training file.
  Uses relative frequencies to calculate probabilities.
  Input:
    (str): csv training file name (known or unmatched)
  Ouput
    (lst): list of tuples of the form ((similarity_tuple), probability))
  '''
  sim_tuples = get_sim_tuples(filename)
  rv = {}
  n = len(sim_tuples)

  for t in sim_tuples:
    if t not in rv:
      rv[t] = 1/n
    else:
      rv[t] += 1/n

  return rv


def get_match_unmatch_probs(unmatched_file, known_links_file):
  '''
  Puts together the match and unmatched probabilities for similarity
  tuples from unmatched and known training data.
  Input:
    (str): csv file name for unmatched training data
    (str): csv file name for matched training data
  Output:
    (tuple): tuple of the form (lst of similarity tuples, lst of 
    probability tuples)
  '''
  matched = est_prob(known_links_file)
  unmatched = est_prob(unmatched_file)
  probs = []
  sim_tups = []

  for i in matched:
    for j in unmatched:
      if i == j:
        tup = (i, matched[i], unmatched[j])
        if tup not in probs:
          probs.append(tup)
          sim_tups.append(i)

      elif i not in unmatched:
        tup = (i, matched[i], 0.0)
        if tup not in probs:
          probs.append(tup)
          sim_tups.append(i)

      elif j not in matched:
        tup = (j, 0.0, unmatched[j])
        if tup not in probs:
          probs.append(tup)
          sim_tups.append(j)

  return sim_tups, probs


def classifier(unmatched_file, known_links_file, mu, lambda_):
  '''
  Computes a dictionary that maps each similarity tuple to a value
  of "match", "possible match", or "unmatch".
  Inputs:
    (str): csv file name for unmatched training data
    (str): csv file name for matched training data
    (float): mu, the maximum false positive rate
    (float): lambda_, the maximum false negative rate
  Output:
    (dict): classifier for all possible similarity tuples
  '''

  sim_tups, prob_tuples = get_match_unmatch_probs(unmatched_file,known_links_file) 
  comb = combination(["low", "medium", "high"]) 
  rv = {}

  # 1) Label tuples with un/matched prob = 0
  for t in comb:
    if t not in sim_tups:
      rv[t] = "possible match"

  # 2) Sort remaining tuples
  sorted_tuples = util.sort_prob_tuples(prob_tuples)

  # 3) Label matches
  sum_m = 0

  for tuple in sorted_tuples:
    sim, _, unmatch_prob = tuple
    sum_m += unmatch_prob
    if sum_m <= mu:
      rv[sim] = "match"
    else:
      break

  # 4) Label unmatches
  sum_u = 0

  for tuple in sorted_tuples[::-1]:
    sim, match_prob, _ = tuple
    sum_u += match_prob
    if sum_u <= lambda_ and sim not in rv:
      rv[sim] = "unmatch"
    elif sum_u <= lambda_ and sim in rv: # Label overlap cases
      rv[sim] = "match"
    else:
      break

  # 5) Label leftover tuples as possible matches
  for tuple in sorted_tuples:
    sim, _, _ = tuple
    if sim not in rv:
      rv[sim] = "possible match"
  
  return rv