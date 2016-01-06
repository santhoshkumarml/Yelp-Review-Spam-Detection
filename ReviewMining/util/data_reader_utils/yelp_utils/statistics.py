'''
Created on Dec 15, 2014

@author: santhosh
'''
import networkx as nx
from util import SIAUtil
from util.GraphUtil import SuperGraph
from datetime import datetime
from util.data_reader_utils.yelp_utils import YelpDataReader
import sys

if __name__ == '__main__':
    inputFileName = sys.argv[1]
    beforeGraphPopulationTime = datetime.now()
    #(parentUserIdToUserDict,parentBusinessIdToBusinessDict,parent_reviews) = dataReader.parseAndCreateObjects(inputFileName)
    scr = YelpDataReader.YelpDataReader()
    (parentUserIdToUserDict,parentBusinessIdToBusinessDict,parent_reviews) =scr.readData(inputFileName)
    wholeGraph = SuperGraph.createGraph(parentUserIdToUserDict, parentBusinessIdToBusinessDict, parent_reviews)
    afterGraphPopulationTime = datetime.now()
    beforeStatisticsGenerationTime = datetime.now()

    print'----------------------Number of Users, Businesses, Reviews----------------------------------------------------------------------'
    print 'Number of Users- ', len(parentUserIdToUserDict.keys()),\
    'Number of Businesses- ', len(parentBusinessIdToBusinessDict.keys()),\
    'Number of Reviews- ', len(parent_reviews)
    print'----------------------Component Sizes----------------------------------------------------------------------'
    cc = sorted(nx.connected_component_subgraphs(wholeGraph,False), key=len, reverse=True)
    lenListComponents = [len(c.nodes()) for c in cc ]
    print lenListComponents
    G = wholeGraph
    print'----------------------User to Neighbors Degree--------------------------------------------------------------'
#     for node in G.nodes():
#         if node.getNodeType() == USER:
#             userToDegreeDict[node] = len(G.neighbors(node))
#         else:
#             businessToDegreeDict[node] = len(G.neighbors(node))
#
#     for user in userToDegreeDict.keys():
#         print user.getId(),' ',userToDegreeDict[i]

    userDegreeDistribution = [len(G.neighbors(node)) for node in G.nodes() if node[1] == SIAUtil.USER]
    userDegreeDistribution = sorted(userDegreeDistribution, reverse=True)
    print userDegreeDistribution
    print'----------------------Business to Neighbors Degree----------------------------------------------------------'
#     for business in businessToDegreeDict.keys():
#         print business.getName(),' ',businessToDegreeDict[i]

    businessDegreeDistribution = [len(G.neighbors(node)) for node in G.nodes() if node[1] == SIAUtil.PRODUCT]
    businessDegreeDistribution = sorted(businessDegreeDistribution, reverse=True)
    print businessDegreeDistribution
