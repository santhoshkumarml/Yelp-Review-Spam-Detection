'''
Created on Nov 17, 2014

@author: Santhosh Kumar
'''
##################VARIABLES#############################

from datetime import datetime
import sys

from LBP import LBP
import matplotlib.pyplot as plt
import networkx as nx
from util import OldGraphUtil
from util import SIAUtil


inputFileName = sys.argv[1]
RECOMMENDED_REVIEW_COLOR = 'black'
NOT_RECOMMENDED_REVIEW_COLOR = 'red'
USER_NODE_COLOR = 'green'
PRODUCT_NODE_COLOR = 'blue'
##################FUNCTIONS#############################
def paintWithLabels(graph,nodetoNodeLabelDict, nodecolor='red', edgecolor='blue'):
    nx.draw(graph,pos=nx.spring_layout(graph), with_labels=True,\
             node_color=nodecolor,edge_color=edgecolor, alpha=0.5, width=2.0,\
              labels=nodetoNodeLabelDict)
    plt.show()

def paint(graph, nodecolor='red', edgecolor='blue'):
    nx.draw(graph,pos=nx.spring_layout(graph), with_labels=True,\
             node_color=nodecolor,edge_color=edgecolor, alpha=1.0, width=10.0)
    plt.show()
################## MAIN #################################
#########################################################
def run(inputFileDir, rdr):
    beforeGraphPopulationTime = datetime.now()
    (parentUserIdToUserDict,parentBusinessIdToBusinessDict,parent_reviews) = rdr.readData(inputFileDir)
    wholeGraph = OldGraphUtil.createGraph(parentUserIdToUserDict, parentBusinessIdToBusinessDict, parent_reviews)
    afterGraphPopulationTime = datetime.now()
    beforeStatisticsGenerationTime = datetime.now()

    print'----------------------Number of Users, Businesses, Reviews----------------------------------------------------------------------'
    print 'Number of Users- ', len(parentUserIdToUserDict.keys()),\
     'Number of Businesses- ', len(parentBusinessIdToBusinessDict.keys()),\
     'Number of Reviews- ', len(parent_reviews)
    print'----------------------Component Sizes----------------------------------------------------------------------'
    cc = sorted(nx.connected_component_subgraphs(wholeGraph,False), key=len, reverse=True)
    lenListComponents = [len(c.nodes()) for c in cc if len(c.nodes())>1 ]
    print lenListComponents
    G = wholeGraph
    #G = cc[1]
    #print'----------------------User to Neighbors Degree--------------------------------------------------------------'
    #for node in G.nodes():
    #    if node.getNodeType() == USER:
    #        userToDegreeDict[node] = len(G.neighbors(node))
    #    else:
    #        businessToDegreeDict[node] = len(G.neighbors(node))

    #for user in userToDegreeDict.keys():
    #    print user.getId(),' ',userToDegreeDict[i]

    # userDegreeDistribution = [len(G.neighbors(node)) for node in G.nodes() if node.getNodeType() == SIAUtil.USER]
    #print userDegreeDistribution
    #print'----------------------Business to Neighbors Degree----------------------------------------------------------'
    #for business in businessToDegreeDict.keys():
    #    print business.getName(),' ',businessToDegreeDict[i]

    # businessDegreeDistribution = [len(G.neighbors(node)) for node in G.nodes() if node.getNodeType() == SIAUtil.PRODUCT]
    #print businessDegreeDistribution
    # print'----------------------Review Sentiment Distribution----------------------------------------------------------'
    # reviewSentimentDistribution = [ G.get_edge_data(*edge)[SIAUtil.REVIEW_EDGE_DICT_CONST].getRating()\
    #                                 G.get_edge_data(*edge)[SIAUtil.REVIEW_EDGE_DICT_CONST].getReviewSentiment(),\
    #                                 G.get_edge_data(*edge)[SIAUtil.REVIEW_EDGE_DICT_CONST].isRecommended())\
    #                                  for edge in G.edges()]
    # print reviewSentimentDistribution
    # print '---------------------- Mean And Variance of the Distributions ----------------------------------------------------------'
    # print 'Average Size Of a Component - ', numpy.mean(numpy.array(lenListComponents)),'Variance Of Component Size - ', numpy.var(numpy.array(lenListComponents))
    # print 'Average Degree Of a User - ',numpy.mean(numpy.array(userDegreeDistribution)),'Variance Of User Degree - ', numpy.var(numpy.array(userDegreeDistribution))
    # print 'Average Degree Of a Business - ',numpy.mean(numpy.array(businessDegreeDistribution)),'Variance Of Business Degree - ', numpy.var(numpy.array(businessDegreeDistribution))
    print'------------------------------------------------------------------------------------------------------------'
    afterStatisticsGenerationTime = datetime.now()
    ##########################################################
    beforeLBPRunTime = datetime.now()
    lbp = LBP(G)
    print 'positive parent_reviews', len([lbp.getEdgeDataForNodes(*edge)\
                                    for edge in G.edges()\
                                  if lbp.getEdgeDataForNodes(*edge).getReviewSentiment()\
                                   == SIAUtil.REVIEW_TYPE_POSITIVE])
    print 'Negative parent_reviews', len([lbp.getEdgeDataForNodes(*edge)\
                                    for edge in G.edges()\
                                  if lbp.getEdgeDataForNodes(*edge).getReviewSentiment()\
                                   == SIAUtil.REVIEW_TYPE_NEGATIVE])
    ##################ALGO_START################
    lbp.doBeliefPropagationIterative(1)
    (fakeUsers,honestUsers,unclassifiedUsers,\
     badProducts,goodProducts,unclassifiedProducts,\
     fakeReviewEdges,realReviewEdges,unclassifiedReviewEdges) = lbp.calculateBeliefVals()

    fakeReviews = [lbp.getEdgeDataForNodes(*edge) for edge in fakeReviewEdges]
    realReviews = [lbp.getEdgeDataForNodes(*edge) for edge in realReviewEdges]
    unclassifiedReviews = [lbp.getEdgeDataForNodes(*edge) for edge in unclassifiedReviewEdges]
    ##################ALGO_END################
    print 'fakeUsers=', len(fakeUsers)
    print 'honestUsers=', len(honestUsers)
    print 'unclassfiedUsers=', len(unclassifiedUsers)
    print 'goodProducts=', len(goodProducts)
    print 'badProducts=', len(badProducts)
    print 'unclassfiedProducts=', len(unclassifiedProducts)
    print 'fakeReviews=', len(fakeReviews)
    print 'realReviews=', len(realReviews)
    print 'unclassfiedReviews=', len(unclassifiedReviews)
    ##################Accuracy calculation#################
    positiveReviewsInFakeReviews = [review for review in fakeReviews\
                                  if lbp.getEdgeDataForNodes(lbp.getUser(review.getUserId()),\
                                                             lbp.getBusiness(review.getBusinessID())).getReviewSentiment() \
                                    == SIAUtil.REVIEW_TYPE_POSITIVE]
    negativeReviewsInFakeReviews = [review for review in fakeReviews\
                                  if lbp.getEdgeDataForNodes(lbp.getUser(review.getUserId()),\
                                                             lbp.getBusiness(review.getBusinessID())).getReviewSentiment() \
                                    == SIAUtil.REVIEW_TYPE_NEGATIVE]
    realReviewsInFakeReviews = [review for review in fakeReviews\
                                  if lbp.getEdgeDataForNodes(lbp.getUser(review.getUserId()),\
                                                             lbp.getBusiness(review.getBusinessID())).isRecommended()]
    fakeReviewsInRealReviews = [review for review in realReviews\
                                  if not lbp.getEdgeDataForNodes(lbp.getUser(review.getUserId()),\
                                                             lbp.getBusiness(review.getBusinessID())).isRecommended()]
    unclassifiedFakeReviews = [review for review in unclassifiedReviews\
                                  if not lbp.getEdgeDataForNodes(lbp.getUser(review.getUserId()),\
                                                             lbp.getBusiness(review.getBusinessID())).isRecommended()]
    unclassifiedRealReviews = [review for review in unclassifiedReviews\
                                  if lbp.getEdgeDataForNodes(lbp.getUser(review.getUserId()),\
                                                             lbp.getBusiness(review.getBusinessID())).isRecommended()]
    print "Number of Positive Reviews in Fake Reviews",len(positiveReviewsInFakeReviews)
    print "Number of Negative Reviews in Fake Reviews",len(negativeReviewsInFakeReviews)
    print "Number of Real Reviews in Fake Reviews",len(realReviewsInFakeReviews)
    print "Number of Fake Reviews in Real Reviews",len(fakeReviewsInRealReviews)
    print "Number of Fake Reviews in Unclassified Reviews",len(unclassifiedFakeReviews)
    print "Number of Real Reviews in Unclassified Reviews",len(unclassifiedRealReviews)

    afterLBPRunTime = datetime.now()
    ###########################################################
    print'Graph Population time:', afterGraphPopulationTime-beforeGraphPopulationTime,\
    'Statistics Generation Time:', afterStatisticsGenerationTime-beforeStatisticsGenerationTime,\
    'Algo run Time:', afterLBPRunTime-beforeLBPRunTime
    # nodetoNodeLabelDict = {node:node.getName() for node in G.nodes()}
    # ncolors = [USER_NODE_COLOR if x.getNodeType()==SIAUtil.USER else PRODUCT_NODE_COLOR for x in G.nodes()]
    # ecolors = [RECOMMENDED_REVIEW_COLOR \
    #              if lbp.getEdgeDataForNodes(x1,x2).isRecommended() \
    #                else NOT_RECOMMENDED_REVIEW_COLOR for (x1,x2) in G.edges()]
    # paintWithLabels(G, nodetoNodeLabelDict, ncolors, ecolors)
