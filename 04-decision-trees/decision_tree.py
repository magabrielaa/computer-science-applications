'''
Building decision trees

María Gabriela Ayala
'''

import math
import sys
import pandas as pd


def go(training_filename, testing_filename):
    '''
    Construct a decision tree using the training data and then apply
    it to the testing data.

    Inputs:
      training_filename (string): the name of the file with the
        training data
      testing_filename (string): the name of the file with the testing
        data

    Returns (list of strings or pandas series of strings): result of
      applying the decision tree to the testing data.
    '''
    df_train = pd.read_csv(training_filename, dtype=str)
    df_test = pd.read_csv(testing_filename, dtype=str)
    target = df_train.columns[-1] 
    remain_att = df_train.columns.tolist()[:-1]
    tree = build_tree(df_train, target, remain_att)
    rv = []

    for _, row in df_test.iterrows():
        label = apply_tree(row, tree)
        rv.append(label)

    return rv


def apply_tree(row, tree):
    '''
    Recursion to apply decision tree to testing data.
    Input:
        (pd Series): row from a DataFrame
        (node Object): decision tree
    Output:
        (str): class label from target attribute after applying
        decision tree to data.
    '''
    #Base case
    if tree.children == {}:
        return tree.class_label
    #Recursion
    else:
        test_val = row[tree.split_col]
        if test_val in tree.children:
            for child_name, child_node in tree.children.items():
                if test_val == child_name:
                    return apply_tree(row, child_node)
        else: 
            return tree.class_label
      

def build_tree(df_train, target, remain_att):
    '''
    Constructs the decision tree from the training data.
    Input:
        (pd DataFrame): training data
        (str): name of target (ie. last column in training dataset)
    Output:
        (node object): decision tree built from training data 
    '''
    class_label = get_label(df_train, target)
    tree = Node(class_label, None, df_train)
    
    #Base cases
    if len(df_train[target].unique()) == 1:
        return tree
    elif all([len(df_train[att].unique()) == 1 for att in remain_att]):
        return tree
    #Recursion
    else:
        split_col, gain_ratio = find_best_split(remain_att, df_train, target)
        if gain_ratio != 0:
            remain_att.remove(split_col) 
            tree.split_col = split_col
            for child_name, child_dataframe in df_train.groupby(split_col):
                child_node = build_tree(child_dataframe, target, remain_att)
                tree.add_child(child_name, child_node)
        else:
            return tree

    return tree


def find_best_split(remain_att, df_train, target):
    '''
    Given the remaining attributes, finds the best splitting column. In the case of 
    a tie where two attributes have the same gain ratio, breaks the tie by choosing 
    the attribute that occurs earlier in the natural ordering for strings
    Inputs:
        (lst): list of remaining attributes at the node
        (pd DataFrame): training data
        (str): name of target (ie. last column in training dataset)
    Output:
        (tuple): name of splitting column attribute, gain ratio
    '''
    c0, c1, parent_c0, parent_c1 = get_counts(df_train, target)
    parent_gini = get_gini(parent_c0, parent_c1)
    rv = {}
    gain_ratio_lst = []
    
    for att in remain_att:
        child_c0 = df_train.groupby(att)[target].apply(lambda x: x[x == c0].count())
        child_c1 = df_train.groupby(att)[target].apply(lambda x: x[x == c1].count())
        sum_gini_weights = 0
        sum_split_info = 0
        for i in range(len(df_train.groupby(att))):
            prob = (child_c0[i] + child_c1[i]) / (parent_c0 + parent_c1)
            child_gini = get_gini(child_c0[i], child_c1[i])
            sum_gini_weights += prob * child_gini
            sum_split_info += (prob * math.log2(prob)) * -1
        if sum_split_info != 0:
            gain_ratio = (parent_gini - sum_gini_weights) / sum_split_info
        else:
            gain_ratio = 0
        rv[att] = gain_ratio
        gain_ratio_lst.append(gain_ratio)

    max_gain_ratio = max(gain_ratio_lst)
    # Breaking tie mechanism
    possible_split_cols = [] 
    for att, gain_ratio in rv.items():
        if gain_ratio == max_gain_ratio:
            possible_split_cols.append(att)

    if len(possible_split_cols) == 1:
        return possible_split_cols[0], rv[possible_split_cols[0]]
    else:
        return min(possible_split_cols), rv[min(possible_split_cols)] 


def get_gini(c0, c1):
    '''
    Calculates gini coefficient.
    '''
    n = c0 + c1
    prob_c0 = c0/n
    prob_c1 = c1/n
    
    return 1 - (prob_c0**2 + prob_c1**2)


def get_counts(df_train, target):
    '''
    Finds the unique values c0 and c1 for the binary target column.
    Computes the frequencies of each.
    Input:
        (pd DataFrame): training data
        (str): name of target (ie. last column in training dataset)
    Ouput:
        (tuple): c0, c1, frequency of c0, frequency of c1
    '''
    c0 = df_train[target].unique()[0]
    c1 = df_train[target].unique()[1]
    c0_count = df_train[target].value_counts()[c0]
    c1_count = df_train[target].value_counts()[c1]

    return c0, c1, c0_count, c1_count


def get_label(df_train, target):
    '''
    Finds the maximum value count for the target class to set as a default 
    value. In the case of a tie, chooses the value that occurs earlier 
    in the natural ordering for strings
    Input:
        (pd DataFrame): training data
        (str): name of target (ie. last column in training dataset)
    Output:
        (str): class label
    '''
    if len(df_train[target].unique()) == 1:
        class_label = df_train[target].unique()[0]
    else:
        c0, c1, c0_count, c1_count = get_counts(df_train, target)

        if c0_count > c1_count: 
            class_label = c0
        elif c1 > c0:
            class_label = c1
        else:
            class_label = min(c0,c1)   
        
    return class_label


class Node:
    '''
    A class representing nodes of a decision tree and child nodes which
    are instances of the Node class themselves.
    '''
    def __init__(self, class_label, split_col, data):
        '''
        Constructor of the Node class.
        '''
        self.class_label = class_label
        self.split_col = split_col
        self.data = data
        self.children = {}
    
    def add_child(self, child_name, child_df):
        '''
        Method for adding children to a node in a dictionary structure.
        '''
        self.children[child_name] = child_df    
    
    def __str__(self):
        '''
        String representation of the Node class to visualize root and children.
        '''
        s = "\nDECISION TREE:\n\n├──Split Column: " + self.split_col + "\n├──Default label: " \
            + self.class_label + "\n│"

        for i, (child_name, child_node) in enumerate(self.children.items()):
            s += "\n├─────Child " + f'# {i+1}' + "\n├─────Child value: " + child_name + \
            "\n├─────Child label: " + child_node.class_label + \
                "\n│\n├────────Grandchild split column: " + child_node.split_col + "\n│"
            for j, (grandchild_name, grandchild_node) in enumerate(child_node.children.items()):
                s+= "\n├────────Grandchild " + f'# {j+1}' + \
                "\n├────────Grandchild name: " + grandchild_name + \
                    "\n├────────Grandchild label: " + grandchild_node.class_label + "\n│"
        
        return s

###########


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python3 {} <training filename> <testing filename>".format(
            sys.argv[0]))
        sys.exit(1)

    for result in go(sys.argv[1], sys.argv[2]):
        print(result)