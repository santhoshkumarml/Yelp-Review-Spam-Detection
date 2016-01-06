'''
Created on Nov 25, 2014

@author: Santhosh Kumar
'''

from __future__ import division

from copy import deepcopy, copy
from datetime import datetime
import sys
from threading import Thread

from graph_algo.lbp.LBP import LBP
from util import OldGraphUtil
from util import SIAUtil
from util.OldGraphUtil import TimeBasedGraph

###################################################Parallelize LBP Run Using Thread######################################################
class LBPRunnerThread(Thread):
    def __init__(self, graph, limit, name='LBPRunner'):
        super(LBPRunnerThread,self).__init__()
        self.graph = graph
        self.name = name
        self.limit = limit
        self.to_be_removed_usr_bnss_edges = set()

    def getFakeEdgesData(self):
        return self.to_be_removed_usr_bnss_edges

    def runLBP(self):
        threadedLBP = LBP(self.graph)
        threadedLBP.doBeliefPropagationIterative(self.limit)

        (fakeUsers, honestUsers, unclassifiedUsers, badProducts,
         goodProducts, unclassifiedProducts, fakeReviewEdges,
         realReviewEdges, unclassifiedReviewEdges) = threadedLBP.calculateBeliefVals()

        self.to_be_removed_usr_bnss_edges = set([(threadedLBP.getEdgeDataForNodes(*edge).getUserId(),\
                                                       threadedLBP.getEdgeDataForNodes(*edge).getBusinessID())\
                             for edge in fakeReviewEdges])
        print len(self.to_be_removed_usr_bnss_edges)

    def run(self):
        print "Starting LBP " + self.name + " " + str(datetime.now())
        self.runLBP()
        print "Exiting " + self.name + " " + str(datetime.now())

###################################################INITIALIZE_PREMILINARY_STEPS##########################################################
def initialize(inputFileDir, rdr):
    (parentUserIdToUserDict, parentBusinessIdToBusinessDict, parent_reviews) =\
        rdr.readData(inputFileDir)
    print len(parent_reviews)
    bnssEdited = 0
    for bnssId in parentBusinessIdToBusinessDict.iterkeys():
        if bnssId in parentBusinessIdToBusinessDict:
            parentBusinessIdToBusinessDict[bnssId].setRating(parentBusinessIdToBusinessDict[bnssId].getRating())
            bnssEdited+=1
    print bnssEdited
    parent_graph = OldGraphUtil.createGraph(parentUserIdToUserDict,parentBusinessIdToBusinessDict,parent_reviews)

#     unnecessary_reviews = set()
#     cc = sorted(networkx.connected_component_subgraphs(parent_graph,False), key=len, reverse=True)
#     for g in cc:
#         g.initializeDicts()
#
#     for g in cc:
#         usr_count = g.getUserCount()
#         bnss_count = g.getBusinessCount()
#         if(usr_count==1):
#             usr = g.getUser(g.getUserIds()[0])
#             for bnss in g.neighbors(usr):
#                 review = g.getReview(usr.getId(),bnss.getId())
#                 unnecessary_reviews.add(review.getId())
#         if(bnss_count==1):
#             bnss = g.getBusiness(g.getBusinessIds()[0])
#             for usr in g.neighbors(bnss):
#                 review = g.getReview(usr.getId(),bnss.getId())
#                 unnecessary_reviews.add(review.getId())
#     print len(unnecessary_reviews)

#     cross_9_months_graphs = SIAUtil.createTimeBasedGraph(parentUserIdToUserDict, parentBusinessIdToBusinessDict, parent_reviews, '9-M')
    cross_time_graphs = OldGraphUtil.createTimeBasedGraph(parentUserIdToUserDict,\
                                                          parentBusinessIdToBusinessDict,\
                                                           parent_reviews, '1-Y')
    beforeThreadTime = datetime.now()
    cross_time_lbp_runner_threads = []
    for time_key in cross_time_graphs.iterkeys():
        print '----------------------------------GRAPH-', time_key, '---------------------------------------------\n'
        lbp_runner = LBPRunnerThread(cross_time_graphs[time_key], 50, 'Initial LBP Runner for Time'+str(time_key))
        cross_time_lbp_runner_threads.append(lbp_runner)
        lbp_runner.start()
    for lbp_runner in cross_time_lbp_runner_threads:
        lbp_runner.join()
    afterThreadTime = datetime.now()
    print 'Time to be reduced',afterThreadTime-beforeThreadTime
    return (cross_time_graphs, parent_graph)

###################################################################DATASTRUCTURES################################################################################
def calculateCrossTimeDs(cross_time_graphs):
    bnss_score_all_time_map = dict()
    for time_key in cross_time_graphs.iterkeys():
        bnss_score_map_for_time = {bnss.getId():bnss.getScore() for bnss in cross_time_graphs[time_key].nodes() if bnss.getNodeType()==SIAUtil.PRODUCT}
        for bnss_key in bnss_score_map_for_time.iterkeys():
            if bnss_key not in bnss_score_all_time_map:
                bnss_score_all_time_map[bnss_key] = dict()
            time_score_map = bnss_score_all_time_map[bnss_key]
            time_score_map[time_key] = bnss_score_map_for_time[bnss_key]
    return bnss_score_all_time_map

################################################ALGO FOR MERGE###############################################################
def calculateInterestingBusinessStatistics(cross_time_graphs, not_mergeable_businessids, bnss_score_all_time_map):
    interesting_bnss_across_time = set([bnss_key for time_key in not_mergeable_businessids for bnss_key in not_mergeable_businessids[time_key]])

    bnss_score_across_time_with_interestingMarked = dict()

    for bnss_key in interesting_bnss_across_time:
        score_across_time_with_intersting_marked = { time_key:(bnss_score_all_time_map[bnss_key][time_key],(0,0),True) \
                                                   if time_key in bnss_score_all_time_map[bnss_key] and time_key in not_mergeable_businessids \
                                                   and bnss_key in not_mergeable_businessids[time_key]\
                                                   else '-' if time_key not in bnss_score_all_time_map[bnss_key] \
                                                   else (bnss_score_all_time_map[bnss_key][time_key],(0,0),False) \
                                                   for time_key in cross_time_graphs.iterkeys()}
        bnss_score_across_time_with_interestingMarked[bnss_key] = score_across_time_with_intersting_marked


    for time_key in cross_time_graphs:
        graph = cross_time_graphs[time_key]
        dummy_lbp = LBP(graph)
        (fakeUsers,honestUsers,unclassifiedUsers,\
            badProducts,goodProducts,unclassifiedProducts,\
            fakeReviewEdges,realReviewEdges,unclassifiedReviewEdges) = dummy_lbp.calculateBeliefVals()
        for fakeReviewEdge in fakeReviewEdges:
            (siaObject1,siaObject2) = fakeReviewEdge
            if siaObject1.getNodeType() == SIAUtil.PRODUCT:
                bnssIdFromEdge = siaObject1.getId()
                if bnssIdFromEdge in bnss_score_across_time_with_interestingMarked:
                    score,(edge_sentiment_negative,edge_sentiment_positive),isInteresting = bnss_score_across_time_with_interestingMarked[bnssIdFromEdge][time_key]
                    if dummy_lbp.getEdgeDataForNodes(*fakeReviewEdge).getReviewSentiment() == SIAUtil.REVIEW_TYPE_NEGATIVE:
                        edge_sentiment_negative+=1
                    else:
                        edge_sentiment_positive+=1
                    bnss_score_across_time_with_interestingMarked[bnssIdFromEdge][time_key] = score,(edge_sentiment_negative,edge_sentiment_positive),isInteresting
                else:
                    bnssIdFromEdge = siaObject2.getId()
                    if bnssIdFromEdge in bnss_score_across_time_with_interestingMarked:
                        score,(edge_sentiment_negative,edge_sentiment_positive),isInteresting = bnss_score_across_time_with_interestingMarked[bnssIdFromEdge][time_key]
                        if dummy_lbp.getEdgeDataForNodes(*fakeReviewEdge).getReviewSentiment() == SIAUtil.REVIEW_TYPE_NEGATIVE:
                            edge_sentiment_negative+=1
                        else:
                            edge_sentiment_positive+=1
                        bnss_score_across_time_with_interestingMarked[bnssIdFromEdge][time_key] = score,(edge_sentiment_negative,edge_sentiment_positive),isInteresting
    print bnss_score_across_time_with_interestingMarked


def calculateMergeAbleAndNotMergeableBusinessesAcrossTime(cross_time_graphs, parent_graph, bnss_score_all_time_map):
    # calculate interesting businesses across time
    mergeable_businessids = dict()
    not_mergeable_businessids = dict()
    for bnss_key in bnss_score_all_time_map.iterkeys():
        time_score_map = bnss_score_all_time_map[bnss_key]
        scores = [time_score_map[time_key][1] for time_key in time_score_map.iterkeys()]
        good_scores = OldGraphUtil.rm_outlier(scores)
#         print 'IN: ', scores #  REMOVE
#         print 'OP: ', good_scores
#         print '*'*10
        for time_key in time_score_map.iterkeys():
            score = time_score_map[time_key][1]
            if(score in good_scores):
                if time_key not in mergeable_businessids:
                    mergeable_businessids[time_key] = set()
                mergeable_businessids[time_key].add(bnss_key)
            else:
                if time_key not in not_mergeable_businessids:
                    not_mergeable_businessids[time_key] = set()
                not_mergeable_businessids[time_key].add(bnss_key)

    for time_key in not_mergeable_businessids.iterkeys():
        print 'Interesting businesses in  time:', time_key,len(not_mergeable_businessids[time_key])

    for time_key in mergeable_businessids.iterkeys():
        print 'Not Interesting businesses in time:', time_key,len(mergeable_businessids[time_key])
    return (mergeable_businessids,not_mergeable_businessids)

def mergeTimeBasedGraphsWithMergeableIds(mergeable_businessids, cross_time_graphs):
    alltimeD_access_merge_graph = TimeBasedGraph()
    all_time_userIdToUserDict = dict()
    all_time_bnssIdToBnssDict = dict()
    for time_key in cross_time_graphs.iterkeys():
        for siaObject in cross_time_graphs[time_key].nodes():
            if siaObject.getId() in all_time_userIdToUserDict or siaObject.getId() in all_time_bnssIdToBnssDict:
                continue
            newSiaObject = copy(siaObject)
            newSiaObject.reset()
            if(newSiaObject.getNodeType() == SIAUtil.USER):
                all_time_userIdToUserDict[newSiaObject.getId()] = newSiaObject
            else:
                all_time_bnssIdToBnssDict[newSiaObject.getId()] = newSiaObject
            alltimeD_access_merge_graph.add_node(newSiaObject)

    alltimeD_access_merge_graph.initialize(all_time_userIdToUserDict, all_time_bnssIdToBnssDict)
    # create a new super graph with all nodes
    # whatever businesses did not drastically change, get all the edges
    # of the business and add them to new super graph
    for time_key in mergeable_businessids:
            graph = cross_time_graphs[time_key]
            for bnssid in mergeable_businessids[time_key]:
                bnss = graph.getBusiness(bnssid)
                usrs = graph.neighbors(bnss)
                for usr in usrs:
                    review = deepcopy(graph.get_edge_data(usr,bnss)[SIAUtil.REVIEW_EDGE_DICT_CONST])
                    alltimeD_access_merge_graph.add_edge(alltimeD_access_merge_graph.getBusiness(bnss.getId()),\
                                                         alltimeD_access_merge_graph.getUser(usr.getId()),\
                                                          {SIAUtil.REVIEW_EDGE_DICT_CONST:review})
                    graph.remove_edge(usr,bnss)

    print len(alltimeD_access_merge_graph.nodes()),len(alltimeD_access_merge_graph.edges())

    return alltimeD_access_merge_graph

def mergeTimeBasedGraphsWithNotMergeableIds(alltimeD_access_merge_graph,not_mergeable_businessids, cross_time_graphs):
    # whatever businesses did drastically change,
    # we will copy the super graph and try adding these edges to the copied
    # graph and run LBP
    to_be_removed_edge_between_user_bnss = set()

    #copy_merge_lbp_runner_threads = []
    beforeThreadTime = datetime.now()
    for time_key in not_mergeable_businessids:
        copied_all_timeD_access_merge_graph =  deepcopy(alltimeD_access_merge_graph)
        graph = cross_time_graphs[time_key]
        for bnssid in not_mergeable_businessids[time_key]:
            bnss = graph.getBusiness(bnssid)
            usrs = graph.neighbors(bnss)
            for usr in usrs:
                review = deepcopy(graph.get_edge_data(usr,bnss)[SIAUtil.REVIEW_EDGE_DICT_CONST])
                copied_all_timeD_access_merge_graph.add_edge(copied_all_timeD_access_merge_graph.getBusiness(bnss.getId()),\
                                                             copied_all_timeD_access_merge_graph.getUser(usr.getId()),
                                                             {SIAUtil.REVIEW_EDGE_DICT_CONST:review})
        copy_merge_lbp = LBP(copied_all_timeD_access_merge_graph)
        copy_merge_lbp.doBeliefPropagationIterative(50)
        (fakeUsers, honestUsers,unclassifiedUsers,\
         badProducts,goodProducts, unclassifiedProducts,\
         fakeReviewEdges, realReviewEdges,unclassifiedReviewEdges) = copy_merge_lbp.calculateBeliefVals()
        for edge in fakeReviewEdges:
            (s1,s2) = edge
            if s1.getNodeType() == SIAUtil.USER:
                to_be_removed_edge_between_user_bnss.add((s1.getId(),s2.getId()))
            else:
                to_be_removed_edge_between_user_bnss.add((s2.getId(),s1.getId()))
#         copy_merge_lbp_runner = LBPRunnerThread(copied_all_timeD_access_merge_graph, 25, 'LBP Runner For Not mergeableIds'+str(time_key))
#         copy_merge_lbp_runner_threads.append(copy_merge_lbp_runner)
#         copy_merge_lbp_runner.start()


#     for copy_merge_lbp_runner in copy_merge_lbp_runner_threads:
#         copy_merge_lbp_runner.join()

    afterThreadTime = datetime.now()
    print 'Time to be reduced', afterThreadTime-beforeThreadTime

#     for copy_merge_lbp_runner in copy_merge_lbp_runner_threads:
#         print 'Copy merge runner', len(copy_merge_lbp_runner.getFakeEdgesData())
#         to_be_removed_edge_between_user_bnss = to_be_removed_edge_between_user_bnss.union(copy_merge_lbp_runner.getFakeEdgesData())

    #from the drastically change businesses we have find out all fake edges in the above step
    # without them add rest of the edges to the super graph and run LBP on it
    for time_key in not_mergeable_businessids:
        graph = cross_time_graphs[time_key]
        for bnssid in not_mergeable_businessids[time_key]:
            bnss = graph.getBusiness(bnssid)
            usrs = graph.neighbors(bnss)
            for usr in usrs:
                if (usr.getId(),bnss.getId()) not in to_be_removed_edge_between_user_bnss:
                    review = deepcopy(graph.get_edge_data(usr,bnss)[SIAUtil.REVIEW_EDGE_DICT_CONST])
                    alltimeD_access_merge_graph.add_edge(alltimeD_access_merge_graph.getBusiness(bnss.getId()),\
                                                         alltimeD_access_merge_graph.getUser(usr.getId()),\
                                                          {SIAUtil.REVIEW_EDGE_DICT_CONST:review})

    print "------------------------------------Running Final Merge LBP--------------------------------------"
    merge_lbp = LBP(alltimeD_access_merge_graph)
    merge_lbp.doBeliefPropagationIterative(50)
    (fakeUsers, honestUsers,unclassifiedUsers,\
     badProducts,goodProducts, unclassifiedProducts,\
     fakeReviewEdges, realReviewEdges,unclassifiedReviewEdges) = merge_lbp.calculateBeliefVals()
    for edge in fakeReviewEdges:
        to_be_removed_edge_between_user_bnss.add((merge_lbp.getEdgeDataForNodes(*edge).getUserId(),\
                                                    merge_lbp.getEdgeDataForNodes(*edge).getBusinessID()))
    certifiedRealFromTemporalAlgo = set()
    for edge in realReviewEdges:
        certifiedRealFromTemporalAlgo.add((merge_lbp.getEdgeDataForNodes(*edge).getUserId(),\
                                                    merge_lbp.getEdgeDataForNodes(*edge).getBusinessID()))
    return (to_be_removed_edge_between_user_bnss,certifiedRealFromTemporalAlgo)
#############################################################################################################################
def runParentLBPAndCompareStatistics(certifiedFakesFromTemporalAlgo,certifiedRealFromTemporalAlgo, parent_graph):
    print "------------------------------------Running Parent LBP along with all Time Edges--------------------------------------"
    # run LBP on a non temporal full graph for comparison
    parent_lbp = LBP(parent_graph)
    parent_lbp.doBeliefPropagationIterative(50)
    (parent_lbp_fakeUsers, parent_lbp_honestUsers,parent_lbp_unclassifiedUsers,\
          parent_lbp_badProducts, parent_lbp_goodProducts, parent_lbp_unclassifiedProducts,\
          parent_lbp_fakeReviewEdges, parent_lbp_realReviewEdges, parent_lbp_unclassifiedReviewEdges) = parent_lbp.calculateBeliefVals()

    print "-----------------------------------------------Statistics------------------------------------------------------------------"
    fakeReviewsInParentLBP = set([parent_lbp.getEdgeDataForNodes(*edge).getId() for edge in parent_lbp_fakeReviewEdges])
    realReviewsInParentLBP = set([parent_lbp.getEdgeDataForNodes(*edge).getId() for edge in parent_lbp_realReviewEdges])

    fakeReviewsFromYelp   = set([parent_lbp.getEdgeDataForNodes(*edge).getId() for edge in parent_graph.edges()\
                                  if not parent_lbp.getEdgeDataForNodes(*edge).isRecommended()] )
    realReviewsFromYelp = set([parent_lbp.getEdgeDataForNodes(*edge).getId() for edge in parent_graph.edges()\
                                  if  parent_lbp.getEdgeDataForNodes(*edge).isRecommended()] )
    fakeReviewsFromTemporalAlgo = set([parent_lbp.getReviewIdsForUsrBnssId(usrId, bnssId) for (usrId,bnssId) in certifiedFakesFromTemporalAlgo])
    realReviewsFromTemporalAlgo = set([parent_lbp.getReviewIdsForUsrBnssId(usrId, bnssId) for (usrId,bnssId) in realFromTemporalAlgo])

    totalReviews = len([egde for egde in parent_graph.edges()])

    #Accuracy
    print 'Fake Reviews Temporal Algo',len(fakeReviewsFromTemporalAlgo)
    print 'Fake Reviews LBP',len(fakeReviewsInParentLBP)
    print 'Fake Reviews Yelp', len(fakeReviewsFromYelp)

    print 'Real Reviews Temporal Algo',len(realReviewsFromTemporalAlgo)
    print 'Real Reviews LBP',len(realReviewsInParentLBP)
    print 'Real Reviews Yelp', len(realReviewsFromYelp)

    print 'Intersection of FakeReviews between Yelp with TemporalLBP:', len(fakeReviewsFromYelp&fakeReviewsFromTemporalAlgo)
    print 'Intersection of FakeReviews between Yelp with LBP:', len(fakeReviewsFromYelp&fakeReviewsInParentLBP)
    print 'Intersection of FakeReviews between Temporal LBP with LBP:', len(fakeReviewsFromTemporalAlgo&fakeReviewsInParentLBP)
    print 'Intersection FakeReviews Across Yelp,Temporal and LBP',len(fakeReviewsFromTemporalAlgo&fakeReviewsInParentLBP&fakeReviewsFromYelp)

    print 'Intersection of RealReviews between Yelp with TemporalLBP:', len(realReviewsFromYelp&realReviewsFromTemporalAlgo)
    print 'Intersection of RealReviews between Yelp with LBP:', len(realReviewsFromYelp&realReviewsInParentLBP)
    print 'Intersection of RealReviews between Temporal LBP with LBP:', len(realReviewsFromTemporalAlgo&realReviewsInParentLBP)
    print 'Intersection RealReviews Across Yelp,Temporal and LBP',len(realReviewsFromTemporalAlgo&realReviewsInParentLBP&fakeReviewsFromYelp)


    print 'Fake Review - Yelp-TemporalLBP:',len(fakeReviewsFromYelp-fakeReviewsFromTemporalAlgo)
    print 'Fake Reviews - TemporalLBP-Yelp:',len(fakeReviewsFromTemporalAlgo-fakeReviewsFromYelp)

    print 'Fake Reviews Yelp-LBP:', len(fakeReviewsFromYelp-fakeReviewsInParentLBP)
    print 'Fake Reviews LBP-Yelp:', len(fakeReviewsInParentLBP-fakeReviewsFromYelp)

    print 'Fake Reviews Temporal LBP-LBP:', len(fakeReviewsFromTemporalAlgo-fakeReviewsInParentLBP)
    print 'Fake Reviews LBP-TemporalLBP:', len(fakeReviewsInParentLBP-fakeReviewsFromTemporalAlgo)

    trueNegativesTemporalAlgo = len(realReviewsFromYelp&realReviewsFromTemporalAlgo)
    truePositivesTemporalAlgo = len(fakeReviewsFromYelp&fakeReviewsFromTemporalAlgo)

    trueNegativesLBP = len(realReviewsFromYelp&realReviewsInParentLBP)
    truePositivesLBP = len(fakeReviewsFromYelp&fakeReviewsInParentLBP)

    accuracyOfTemporalAlgo = (truePositivesTemporalAlgo + trueNegativesTemporalAlgo)/totalReviews
    accuracyOfLBP = (truePositivesLBP + trueNegativesLBP)/totalReviews

    precisionOfTemporalAlgo = len(fakeReviewsFromYelp&fakeReviewsFromTemporalAlgo)/len(fakeReviewsFromTemporalAlgo)
    precisionOfLBP = len(fakeReviewsFromYelp&fakeReviewsInParentLBP)/len(fakeReviewsInParentLBP)

    recallOfTemporalAlgo = len(fakeReviewsFromYelp&fakeReviewsFromTemporalAlgo)/len(fakeReviewsFromYelp)
    recallOfLBP = len(fakeReviewsFromYelp&fakeReviewsInParentLBP)/len(fakeReviewsFromYelp)

    F1ScoreOfTemporalAlgo = (2*precisionOfTemporalAlgo*recallOfTemporalAlgo)/(precisionOfTemporalAlgo+recallOfTemporalAlgo)
    F1ScoreOfLBP = (2*precisionOfLBP*recallOfLBP)/(precisionOfLBP+recallOfLBP)

    print 'Accuracy of Temporal LBP',accuracyOfTemporalAlgo
    print 'Accuracy of LBP', accuracyOfLBP

    print 'Precision of Temporal LBP',precisionOfTemporalAlgo
    print 'Precision of LBP', precisionOfLBP

    print 'Recall of Temporal LBP', recallOfTemporalAlgo
    print 'Recall of LBP', recallOfLBP

    print 'F1Score of Temporal LBP',F1ScoreOfTemporalAlgo
    print 'F1Score of LBP',F1ScoreOfLBP

if __name__ == '__main__':
    inputFileName = sys.argv[1]
    #inputFileName = '/media/santhosh/Data/workspace/dm/data/crawl_old/o_new_2.txt'
    #inputFileName = '/media/santhosh/Data/workspace/dm/data/crawl_new/sample_master.txt'
    beforeRunTime = datetime.now()
    #inputFileName = '/home/rami/Downloads/sample_master.txt'

    beforeTemporalTime = datetime.now()
    (cross_graphs, pg) = initialize(inputFileName)
    bnss_all_time_map = calculateCrossTimeDs(cross_graphs)
    (mIds,nonMids) = calculateMergeAbleAndNotMergeableBusinessesAcrossTime(cross_graphs, pg, bnss_all_time_map)
    #calculateInterestingBusinessStatistics(cross_graphs, nonMids, bnss_all_time_map)
    time_merge_graph = mergeTimeBasedGraphsWithMergeableIds(mIds, cross_graphs)
    (fakesFromTemporalAlgo,realFromTemporalAlgo) = mergeTimeBasedGraphsWithNotMergeableIds(time_merge_graph, nonMids, cross_graphs)
    afterTemporalTime = datetime.now()

    beforeParentLBP = datetime.now()
    runParentLBPAndCompareStatistics(fakesFromTemporalAlgo, realFromTemporalAlgo, pg)
    afterParentLBP = datetime.now()

    afterRunTime = datetime.now()

    print 'Total Run Time', afterRunTime-beforeRunTime,\
            'Run Time of Temporal LBP Algo',afterTemporalTime-beforeTemporalTime,\
            'Run Time of LBP Algo',afterParentLBP-beforeParentLBP