'''
Created on Jan 12, 2015

@author: santhosh
'''
from util import SIAUtil
import networkx
from SIAUtil import PRODUCT, USER, REVIEW_EDGE_DICT_CONST
from copy import deepcopy
import re
from datetime import datetime, timedelta
from scipy.stats import bayes_mvs
import numpy as np

class TimeBasedGraph(networkx.Graph):
    def __init__(self, parentUserIdToUserDict=dict(),parentBusinessIdToBusinessDict=dict()):
        super(TimeBasedGraph, self).__init__()
        self.userIdToUserDict = deepcopy(parentUserIdToUserDict)
        self.businessIdToBusinessDict = deepcopy(parentBusinessIdToBusinessDict)
        
    def initialize(self, userIdToUserDict,businessIdToBusinessDict):
        self.userIdToUserDict = userIdToUserDict
        self.businessIdToBusinessDict = businessIdToBusinessDict
    
    def initializeDicts(self):
        for siaObject in self.nodes():
            if siaObject.getNodeType() == USER:
                self.userIdToUserDict[siaObject.getId()] =siaObject
            else:
                self.businessIdToBusinessDict[siaObject.getId()] =siaObject
    
    def getUserCount(self):
        return len(set([node.getId() for node in self.nodes() if node.getNodeType()==USER]))
    
    def getUserIds(self):
        return [node.getId() for node in self.nodes() if node.getNodeType()==USER]
    
    def getBusinessIds(self):
        return [node.getId() for node in self.nodes() if node.getNodeType()==PRODUCT]
    
    def getBusinessCount(self):
        return len(set([node.getId() for node in self.nodes() if node.getNodeType()==PRODUCT]))
        
    def getUser(self,userId):
        return self.userIdToUserDict[userId]
    
    def getBusiness(self, businessId):
        return self.businessIdToBusinessDict[businessId]
    
    def getReview(self,usrId,bnssId):
        return self.get_edge_data(self.getUser(usrId), self.getBusiness(bnssId))[REVIEW_EDGE_DICT_CONST]



def setPriors(G):
    for bnss in G.nodes():
        if bnss.getNodeType() == PRODUCT:
                bnss.setPriorScore()

def createGraph(parentUserIdToUserDict,parentBusinessIdToBusinessDict,\
                 parent_reviews, initializePrirors = True):
    G = TimeBasedGraph(parentUserIdToUserDict, parentBusinessIdToBusinessDict)
    for reviewKey in parent_reviews:
        review = parent_reviews[reviewKey]
        usr = G.getUser(review.getUserId())
        bnss = G.getBusiness(review.getBusinessID())
        G.add_node(usr)
        G.add_node(bnss)
        G.add_edge(bnss, usr, dict({REVIEW_EDGE_DICT_CONST:review}))
    if initializePrirors:
        setPriors(G)
    return G
    
def createTimeBasedGraph(parentUserIdToUserDict,parentBusinessIdToBusinessDict, parent_reviews,\
                          timeSplit ='1-D', initializePriors=True):
    if not re.match('[0-9]+-[DMY]', timeSplit):
        print 'Time Increment does not follow the correct Pattern - Time Increment Set to 1 Day'
        timeSplit ='1-D'

    numeric = int(timeSplit.split('-')[0])
    incrementStr = timeSplit.split('-')[1]
    dayIncrement = 1
    if incrementStr=='D':
        dayIncrement = numeric
    elif incrementStr=='M':
        dayIncrement = numeric*30
    else:
        dayIncrement = numeric*365
        
    minDate =  min([SIAUtil.getDateForReview(r)\
                 for r in parent_reviews.values() ])
    maxDate =  max([SIAUtil.getDateForReview(r)\
                 for r in parent_reviews.values() ])
    cross_time_graphs = dict()
    time_key = 0
    while time_key < ((maxDate-minDate+timedelta(dayIncrement))/dayIncrement).days:
        cross_time_graphs[time_key] = TimeBasedGraph(parentUserIdToUserDict, parentBusinessIdToBusinessDict)
        time_key+=1
    for reviewKey in parent_reviews.iterkeys():
        review = parent_reviews[reviewKey]
        reviewDate = SIAUtil.getDateForReview(review)
        timeDeltaKey = ((reviewDate-minDate)/dayIncrement).days
        timeSplittedgraph = cross_time_graphs[timeDeltaKey]
        usr = timeSplittedgraph.getUser(review.getUserId())
        bnss = timeSplittedgraph.getBusiness(review.getBusinessID())
        timeSplittedgraph.add_node(usr)
        timeSplittedgraph.add_node(bnss)
        timeSplittedgraph.add_edge(usr, bnss, dict({REVIEW_EDGE_DICT_CONST:review}))
    if initializePriors:
        for time_key in cross_time_graphs.iterkeys():
            setPriors(cross_time_graphs[time_key])
    return cross_time_graphs

def rm_outlier(points, threshold=0.45):
    try:
        #diff = [sum([abs(y-x) for x in points]) for y in points]
        diff = [sum([abs(points[j]-points[i])*(len(points)-abs((j-i))/len(points)) for i in range(0, len(points))]) for j in range(0, len(points))]
        avg_diff = sum(diff)/len(diff)
        if avg_diff <= 0: # All values the same, absolute diff is 0
            return points
        percent_diff_from_avg = [abs(x - avg_diff)/avg_diff for x in diff]
        return [points[i] for i in range(0, len(points)) if percent_diff_from_avg[i] <= threshold]
    except:
        return points
    

def rm_outlier3(points, threshold=0.9):
    try:
        confidence = bayes_mvs(rm_outlier2(points), threshold)
        return [points[i] for i in range(0, len(points)) if confidence[i][0] != float('inf')]
    except:
        return points

def rm_outlier2(points, threshold=1.0):
    points_array = np.array(points)
    if len(points_array.shape) == 1:
        points_array = points_array[:,None]
    median = np.median(points_array, axis=0)
    diff_from_median = np.sum((points_array - median)**2, axis=-1)
    diff_from_median = np.sqrt(diff_from_median)
    median_abs_deviation = np.median(diff_from_median)
    if median_abs_deviation == 0:  median_abs_deviation = 0.1 #For div by zero error only
    modified_z_score = 0.6745 * diff_from_median / median_abs_deviation
    return [points[i] for i in range(0, len(points)) if modified_z_score[i] <= threshold]