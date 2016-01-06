'''
@author: Santhosh Kumar Manavasi Lakshminaryanan
'''
'''
 Loopy Belief Propagation
'''
from util import SIAUtil


class LBP(object):
    def __init__(self, graph):
        self.graph = graph
#     def normalizeProductMessages(self):
#         for product in self.graph.nodes():
#             if product.getNodeType() == PRODUCT:
#                 product.normalizeMessages()
#
#     def normalizeUserMessages(self):
#         for user in self.graph.nodes():
#             if user.getNodeType() == USER:
#                 user.normalizeMessages()
    def getUser(self, userId):
        user = self.graph.getUser(userId)
        return user

    def getBusiness(self,businessID):
        business = self.graph.getBusiness(businessID)
        return business

    def getEdgeDataForNodes(self,user,business):
        return self.graph.get_edge_data(user,business)[SIAUtil.REVIEW_EDGE_DICT_CONST]

    def getReviewIdsForUsrBnssId(self, usrId, bnssId):
        return self.getEdgeDataForNodes(self.getUser(usrId), self.getBusiness(bnssId)).getId()

    def getNeighborWithEdges(self, siaObject):
        return [(neighbor,self.graph.get_edge_data(siaObject, neighbor)) \
                for neighbor in self.graph.neighbors(siaObject)]

    #DON't USE - will reach max recursion limit
    def doBeliefPropagationRecursive(self, limit):
        changedProducts = []
        changedUsers = []
        if not (limit==0):
            for user in self.graph.nodes():
                if user.getNodeType() == SIAUtil.USER:
                    changedNodes = user.calculateAndSendMessagesToNeighBors(self.getNeighborWithEdges(user))
                    changedProducts.extend(changedNodes)

            for product in self.graph.nodes():
                if product.getNodeType() == SIAUtil.PRODUCT:
                    changedNodes = product.calculateAndSendMessagesToNeighBors(self.getNeighborWithEdges(product))
                    changedUsers.extend(changedNodes)

            noOfChangedProducts = len(changedProducts)
            noOfChangedUsers = len(changedUsers)
            totalNoOfChangedNodes = noOfChangedProducts+noOfChangedUsers
            if not (totalNoOfChangedNodes==0):
                self.doBeliefPropagation(limit-1)

    def doBeliefPropagationIterative(self, limit):
        while not (limit==0):
            changedProducts = []
            changedUsers = []
            for user in self.graph.nodes():
                if user.getNodeType() == SIAUtil.USER:
                    changedNodes = user.calculateAndSendMessagesToNeighBors(self.getNeighborWithEdges(user))
                    changedProducts.extend(changedNodes)

            for product in self.graph.nodes():
                if product.getNodeType() == SIAUtil.PRODUCT:
                    changedNodes = product.calculateAndSendMessagesToNeighBors(self.getNeighborWithEdges(product))
                    changedUsers.extend(changedNodes)

            noOfChangedProducts = len(changedProducts)
            noOfChangedUsers = len(changedUsers)
            totalNoOfChangedNodes = noOfChangedProducts+noOfChangedUsers

            #print 'changedNodes In This Iteration', totalNoOfChangedNodes
            if (totalNoOfChangedNodes==0):
                break

            limit-=1



    def calculateBeliefVals(self):
        fakeUsers = []
        honestUsers = []
        goodProducts = []
        badProducts = []
        fakeReviews = []
        realReviews = []
        unclassifiedUsers = []
        unclassifiedProducts = []
        unclassifiedReviews = []

        for siaObject in self.graph.nodes():
            siaObject.calculateBeliefVals();
            beliefVal = siaObject.getScore()
            if siaObject.getNodeType() == SIAUtil.USER:
                if(beliefVal[0] > beliefVal[1]):
                    fakeUsers.append(siaObject)
                elif(beliefVal[0] == beliefVal[1]):
                    unclassifiedUsers.append(siaObject)
                else:
                    honestUsers.append(siaObject)
            else:
                if(beliefVal[0] > beliefVal[1]):
                    badProducts.append(siaObject)
                elif(beliefVal[0] == beliefVal[1]):
                    unclassifiedProducts.append(siaObject)
                else:
                    goodProducts.append(siaObject)

        for edge in self.graph.edges():
            review = self.graph.get_edge_data(*edge)[SIAUtil.REVIEW_EDGE_DICT_CONST]
            review.calculateBeliefVals(*edge)
            beliefVal = review.getScore()
            if(beliefVal[0] == beliefVal[1]): #or (fabs(beliefVal[0]-beliefVal[1]) < 0.01):
                unclassifiedReviews.append(edge)
            elif(beliefVal[0] > beliefVal[1]):
                fakeReviews.append(edge)
            else:
                realReviews.append(edge)
        return (fakeUsers,honestUsers,unclassifiedUsers,\
                badProducts,goodProducts,unclassifiedProducts,\
                fakeReviews,realReviews,unclassifiedReviews)