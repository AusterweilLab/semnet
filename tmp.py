import rw
import networkx as nx
import numpy as np
import pickle
import sys

numsubs = int(sys.argv[2])+1

pnumnodes=100
graphs=[]
for filenum in range(50):
    filename="theta_graphs/theta_"+str(filenum)+".pickle"
    fh=open(filename,"r")
    graph=np.array(pickle.load(fh))
    graphs.append(graph)
    fh.close()

prior_items={}
for i in range(100):
    prior_items[i] = i

#pgraph, usf_items = rw.read_csv("./snet/USF_animal_subset.snet")
#pgraph_nx = nx.from_numpy_matrix(pgraph)
#pnumnodes = len(usf_items)

numlists = 3
listlength = 25
numsims = 1
#methods=['rw','goni','chan','kenett','fe','uinvite_flat','uinvite_hierarchical']
methods=['uinvite_hierarchical']

toydata=rw.Data({
        'numx': numlists,
        'trim': listlength })

fitinfo=rw.Fitinfo({
        'prior_method': "betabinomial",
        'zib_p': .5,
        'prior_a': 1,
        'prior_b': 1,
        'startGraph': "goni_valid",
        'goni_size': 2,
        'goni_threshold': 2,
        'followtype': "avg", 
        'prune_limit': np.inf,
        'triangle_limit': np.inf,
        'other_limit': np.inf })

bb_aggregate = rw.Fitinfo({
	'prior_method': "betabinomial",
	'prior_a': 1,
	'prior_b': 1})

# need to use BB(1,1) to ensure no bias in aggregating network!! silly way to do it but that's how it is
priordict = rw.genGraphPrior(graphs, [prior_items]*50, fitinfo=bb_aggregate)
pgraph = rw.priorToGraph(priordict, prior_items)


# generate data for `numsub` participants, each having `numlists` lists of `listlengths` items
seednum=0    # seednum=150 (numsubs*numlists) means start at second sim, etc.
outfile="theta_results_" + str(numsubs) + ".csv"

with open(outfile,'w',0) as fh:
    fh.write("method,simnum,listnum,hit,miss,fa,cr,cost,startseed\n")

    for simnum in range(numsims):
        data = []       # Xs using usf_item indices
        datab = []      # Xs using ss_item indices (nodes only generated by subject)
        numnodes = []
        items = []      # ss_items
        startseed = seednum # for recording

        for sub in range(numsubs):
            Xs = rw.genX(nx.to_networkx_graph(graphs[sub]), toydata, seed=seednum)[0]
            data.append(Xs)

            # renumber dictionary and item list
            itemset = set(rw.flatten_list(Xs))
            numnodes.append(len(itemset))

            ss_items = {}
            convertX = {}
            for itemnum, item in enumerate(itemset):
                ss_items[itemnum] = prior_items[item]
                convertX[item] = itemnum

            items.append(ss_items)

            Xs = [[convertX[i] for i in x] for x in Xs]
            datab.append(Xs)
            
            seednum += numlists
        
        listnum = numsubs
        print simnum, listnum
        flatdata = rw.flatten_list(data[:listnum])
        if 'rw' in methods:
            rw_graph = rw.noHidden(flatdata, pnumnodes)
        if 'goni' in methods:
            goni_graph = rw.goni(flatdata, pnumnodes, td=toydata, valid=0, fitinfo=fitinfo)
        if 'chan' in methods:
            chan_graph = rw.chan(flatdata, pnumnodes)
        if 'kenett' in methods:
            kenett_graph = rw.kenett(flatdata, pnumnodes)
        if 'fe' in methods:
            fe_graph = rw.firstEdge(flatdata, pnumnodes)
        if 'uinvite_hierarchical' in methods:
            uinvite_graphs, priordict = rw.hierarchicalUinvite(datab[:listnum], items[:listnum], numnodes[:listnum], toydata, fitinfo=fitinfo)
            uinvite_group_graph = rw.priorToGraph(priordict, prior_items) #JZ
            for gnum, graph in enumerate(uinvite_graphs):
                uinvite_graphs[gnum] = rw.smallToBigGraph(graph, items[gnum], prior_items)
        if 'uinvite_flat' in methods:
            uinvite_flat_graph, ll = rw.uinvite(flatdata, toydata, pnumnodes, fitinfo=fitinfo)

        truecost = rw.probXhierarchical(data, graphs, [prior_items]*numsubs, toydata)
        
        for method in methods:
            if method=="rw": costlist = [rw.costSDT(rw_graph, pgraph), rw.cost(rw_graph, pgraph)]
            if method=="goni": costlist = [rw.costSDT(goni_graph, pgraph), rw.cost(goni_graph, pgraph)]
            if method=="chan": costlist = [rw.costSDT(chan_graph, pgraph), rw.cost(chan_graph, pgraph)]
            if method=="kenett": costlist = [rw.costSDT(kenett_graph, pgraph), rw.cost(kenett_graph, pgraph)]
            if method=="fe": costlist = [rw.costSDT(fe_graph, pgraph), rw.cost(fe_graph, pgraph)]
            if method=="uinvite_hierarchical": costlist = [rw.costSDT(uinvite_group_graph, pgraph), rw.cost(uinvite_group_graph, pgraph)]
            if method=="uinvite_flat": costlist = [rw.costSDT(uinvite_flat_graph, pgraph), rw.cost(uinvite_flat_graph, pgraph)]

            if method=="uinvite_hierarchical":
                estimatedcost = rw.probXhierarchical(data, uinvite_graphs, [prior_items]*numsubs, toydata)
            else:
                estimatedcost = 0
            
            costlist = rw.flatten_list(costlist)
            fh.write(method + "," + str(simnum) + "," + str(listnum) + "," + str(truecost) + "," + str(estimatedcost))
            for i in costlist:
                fh.write("," + str(i))
            fh.write("," + str(startseed))
            fh.write('\n')
