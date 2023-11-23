#!/usr/bin/python -tt

import pandas as pd
import random
import networkx as nx
import numpy as np
import itertools
import matplotlib.pyplot as plt
import csv
import sys


""""""
def load_data(file):
   return pd.read_csv(file)

"""Checking for free network edges aka people who need to be paired"""
def has_free_edge(edge_df):
    return len(edge_df) != 0

""""Draws from a hat, if the hat created hamiltonian circuits"""
def draw_edges_from_hat(edgelist):
    local_draws = pd.DataFrame(columns=['From', 'To'])
    while has_free_edge(edgelist):
        pick = edgelist.sample(n=1)
        illegal_edges = find_illegal_edges(edgelist, pick)
        edgelist = remove_illegal_edges(edgelist, illegal_edges)
        local_draws = pd.concat([local_draws,pick],ignore_index=True)
    return(local_draws)

"""Find the edges that need to be removed from the graph"""
def find_illegal_edges(edgelist, pick):
    # All ties from this sender
    outgoing = edgelist[edgelist['From'] == pick.iloc[0]['From']]
    # All ties to this recipient
    incoming = edgelist[edgelist['To'] == pick.iloc[0]['To']]
    # Total ties with shared tie included
    illegal = pd.merge(incoming, outgoing, on=['From', 'To'], how='outer', indicator=True).drop('_merge', axis=1)
    return (illegal)

"""Remove those edges from the graph"""
def remove_illegal_edges(edgelist, illegal_edges):
    merged_df = pd.merge(edgelist, illegal_edges, on=['From', 'To'], how='left', indicator=True)
    result_df = merged_df[merged_df['_merge'] != 'both'].drop('_merge', axis=1)
    return result_df

""""Load in the data, add variables,create networks"""
def preprocess(file):
    ## load data file
    global santaData
    santaData = load_data(file)

    ## add full names
    santaData['Giver_Full_Name'] = santaData['Giver_First'] + ' ' + santaData['Giver_Last']
    santaData['Spouse_Full_Name'] = santaData['Spouse_First'] + ' ' + santaData['Spouse_Last']
    ## add a column to capture relationship
    ## Create saturated network
    all_pairs = list(itertools.product(santaData.Giver_Full_Name, repeat=2))
    G = nx.Graph()
    G.add_nodes_from(santaData['Giver_Full_Name'])
    G = G.to_directed()
    G.add_edges_from(all_pairs)
    G.remove_edges_from(nx.selfloop_edges(G))
    ## Create marriage network
    global marriages
    marriages = pd.DataFrame(santaData[['Giver_Full_Name', 'Spouse_Full_Name']])
    marriages = marriages.dropna()
    M = nx.from_pandas_edgelist(marriages, 'Giver_Full_Name', 'Spouse_Full_Name')
    M = M.to_directed()
    ##All possible pairs (without self-loops) minus marriages
    edges_difference = set(G.edges()) - set(M.edges())
    edgelist = pd.DataFrame(edges_difference, columns=['From', 'To'])
    return edgelist

"""Check if algorthim produced satisfactory solution"""
def test_solution(draws):
    global P
    P = nx.DiGraph()
    # Add edges to the graph
    for pair_df in draws:
        edges = draws.to_numpy().tolist()
        P.add_edges_from(edges)
    degrees = [val for (node, val) in P.degree()]
    # is it a cycle?
    continuous_loop = all(x == 2 for x in degrees)
    P_undirected = P.to_undirected()
    number_of_connected_components = nx.number_connected_components(P_undirected)
    n_components = number_of_connected_components == 1
    # Are there any self.loops?
    no_self_loop = not (any(draws.From == draws.To))
    merged_test = pd.merge(draws, marriages, how='inner', left_on="From", right_on="Giver_Full_Name")
    # any marriages?
    no_marriages = len(merged_test[merged_test['To'] == merged_test['Spouse_Full_Name']]) == 0
    return continuous_loop and no_self_loop and no_marriages and not draws.empty and n_components


"""Write to CSV"""
def return_output(take):
    take.to_csv('secretsanta.csv', index=False)

def main(file):
    edgelist = preprocess(file)
    picks = pd.DataFrame(columns=['From','To'])
    while not test_solution(picks):
        picks = draw_edges_from_hat(edgelist)
    take = pd.merge(picks, santaData, how='inner', left_on='From', right_on="Giver_Full_Name")
    plt.show(block=False)
    pos = nx.spring_layout(P)
    nx.draw(P, pos, with_labels=True, font_weight='bold', node_color='skyblue', node_size=800, font_size=8,
           edge_color='red', linewidths=0.8)
    plt.show()
    return_output(take)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    main(file_path)
