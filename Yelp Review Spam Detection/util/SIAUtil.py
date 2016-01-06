'''
Created on Nov 3, 2014

@author: santhosh
'''
from datetime import date, datetime
import numpy
import re


'''
Node Types
'''
USER = 'USER'
PRODUCT = 'PRODUCT'

'''
User Types
'''
USER_TYPE_FRAUD = 0
USER_TYPE_HONEST = 1
USER_TYPES = {USER_TYPE_FRAUD, USER_TYPE_HONEST}
'''
Product Types
'''
PRODUCT_TYPE_BAD = 0
PRODUCT_TYPE_GOOD = 1
PRODUCT_TYPES = {PRODUCT_TYPE_BAD, PRODUCT_TYPE_GOOD}

'''
Review Types
'''
REVIEW_TYPE_FAKE = 0
REVIEW_TYPE_REAL = 1
REVIEW_TYPES = {REVIEW_TYPE_FAKE, REVIEW_TYPE_REAL}


REVIEW_TYPE_NEGATIVE = 0
REVIEW_TYPE_POSITIVE = 1
REVIEW_TYPE_NEUTRAL = 2

REVIEW_EDGE_DICT_CONST = 'review'
EPISOLON = 10 ** -1
COMP_POT = numpy.zeros(shape=(2,2,2),dtype=numpy.float32)
def init_COMP_POT():
    for reviewType in REVIEW_TYPES:
        for userType in USER_TYPES:
            for productType in PRODUCT_TYPES:
                output = 0
                if reviewType == REVIEW_TYPE_NEGATIVE:
                    if userType == USER_TYPE_HONEST:
                        if productType == PRODUCT_TYPE_GOOD:
                            output = EPISOLON
                        else:
                            output = 1-EPISOLON
                    else:
                        if productType == PRODUCT_TYPE_GOOD:
                            output = 0.1#(2*EPISOLON)#0.2
                        else:
                            output = 0.9#(1-2*EPISOLON)
                else:
                    if userType == USER_TYPE_HONEST:
                        if productType == PRODUCT_TYPE_GOOD:
                            output = 1-EPISOLON
                        else:
                            output = EPISOLON
                    else:
                        if productType == PRODUCT_TYPE_GOOD:
                            output = 0.9#(1-2*EPISOLON)
                        else:
                            output =0.1#2*EPISOLON

                COMP_POT[reviewType][userType][productType] = output

class SIAObject(object):
    def __init__(self, score=(0.5, 0.5), NODE_TYPE=USER):
        self.score = score
        self.messages = dict()
        self.nodeType = NODE_TYPE

    def reset(self):
        self.messages.clear()
        self.score = (0.5,0.5)

    def getMessageFromNeighbor(self, neighbor):
        return self.messages[neighbor]

    def addMessages(self, node, message):
        hasChanged = False
        message = self.normalizeMessage(message)
        if node not in self.messages or self.messages[node] != message:
            self.messages[node] = message
            hasChanged = True
        return hasChanged

    def calculateAndSendMessagesToNeighBors(self, neighborsWithEdges):
        changedNeighbors = []
        for neighborWithEdge in neighborsWithEdges:
            (neighbor,edge) = neighborWithEdge
            message = self.calculateMessageForNeighbor(neighborWithEdge);
            if(neighbor.addMessages(self, message)):
                changedNeighbors.append(neighbor)
        return changedNeighbors

    def getScore(self):
        return self.score

    def getNodeType(self):
        return self.nodeType

    def normalizeMessage(self, message):
        normalizingValue = message[0]+message[1]
        message = (message[0]/normalizingValue, message[1]/normalizingValue)
        return message

class SIALink(object):
    def __init__(self, score=(0.5, 0.5)):
        self.score = score

    def getScore(self):
        return self.score

class user(SIAObject):
    def __init__(self, _id, name, usrExtra ='',score=(0.5,0.5)):
        super(user, self).__init__(score, USER)
        self.id = _id
        self.name = name
        self.usrExtra = usrExtra

    def getName(self):
        return self.name

    def getId(self):
        return self.id

    def getUsrExtra(self):
        return self.usrExtra


    def calculateMessageForNeighbor(self, neighborWithEdge):
        allOtherNeighborMessageMultiplication = (1,1)
        (neighbor, edge) = neighborWithEdge
        for messageKey in self.messages.keys():
            if messageKey != neighbor:
                message= self.messages[messageKey]
                allOtherNeighborMessageMultiplication = \
                (allOtherNeighborMessageMultiplication[USER_TYPE_FRAUD]*message[USER_TYPE_FRAUD] , \
                 allOtherNeighborMessageMultiplication[USER_TYPE_HONEST]*message[USER_TYPE_HONEST])
        scoreAddition = (0,0)
        review = edge[REVIEW_EDGE_DICT_CONST]
        for userType in USER_TYPES:
            scoreAddition=\
             (scoreAddition[0]+(COMP_POT[review.getReviewSentiment()][userType][PRODUCT_TYPE_BAD]*self.score[userType]*allOtherNeighborMessageMultiplication[userType]),\
             scoreAddition[1]+(COMP_POT[review.getReviewSentiment()][userType][PRODUCT_TYPE_GOOD]*self.score[userType]*allOtherNeighborMessageMultiplication[userType]))
        return scoreAddition

    def calculateBeliefVals(self):
        allNeighborMessageMultiplication = (1,1)
        for messageKey in self.messages.keys():
            message= self.messages[messageKey]
            allNeighborMessageMultiplication = \
                (allNeighborMessageMultiplication[USER_TYPE_FRAUD]*message[USER_TYPE_FRAUD] , \
                 allNeighborMessageMultiplication[USER_TYPE_HONEST]*message[USER_TYPE_HONEST])
        normalizingValue = (self.score[USER_TYPE_FRAUD]*allNeighborMessageMultiplication[USER_TYPE_FRAUD])+\
        (self.score[USER_TYPE_HONEST]*allNeighborMessageMultiplication[USER_TYPE_HONEST])
        self.score = ((self.score[USER_TYPE_FRAUD]*allNeighborMessageMultiplication[USER_TYPE_FRAUD])/normalizingValue, \
                (self.score[USER_TYPE_HONEST]*allNeighborMessageMultiplication[USER_TYPE_HONEST])/normalizingValue)

class business(SIAObject):
    def __init__(self, _id, name, rating=2.5, url=None, score=(0.5,0.5), reviewCount=0):
        super(business, self).__init__(score, PRODUCT)
        self.id = _id
        self.name = name
        self.rating = rating
        self.url = url
        self.reviewCount = reviewCount

    def setPriorScore(self):
        if self.rating:
            scorePositive = self.rating/5
            self.score = (1-scorePositive,scorePositive)

    def getName(self):
        return self.name

    def getId(self):
        return self.id

    def getRating(self):
        return self.rating

    def setRating(self, rating):
        self.rating = rating

    def getUrl(self):
        return self.url

    def getReviewCount(self):
        return self.reviewCount

    def calculateMessageForNeighbor(self, neighborWithEdge):
        allOtherNeighborMessageMultiplication = (1,1)
        (neighbor, edge) = neighborWithEdge
        for messageKey in self.messages.keys():
            if messageKey != neighbor:
                message= self.messages[messageKey]
                allOtherNeighborMessageMultiplication = \
                (allOtherNeighborMessageMultiplication[PRODUCT_TYPE_BAD]*message[PRODUCT_TYPE_BAD] , \
                 allOtherNeighborMessageMultiplication[PRODUCT_TYPE_GOOD]*message[PRODUCT_TYPE_GOOD])
        review = edge[REVIEW_EDGE_DICT_CONST]
        scoreAddition = (0,0)
        for productType in PRODUCT_TYPES:
            scoreAddition=\
             (scoreAddition[0]+(COMP_POT[review.getReviewSentiment()][USER_TYPE_FRAUD][productType]*self.score[productType]*allOtherNeighborMessageMultiplication[productType]),\
             scoreAddition[1]+(COMP_POT[review.getReviewSentiment()][USER_TYPE_HONEST][productType]*self.score[productType]*allOtherNeighborMessageMultiplication[productType]))
        return scoreAddition

    def calculateBeliefVals(self):
        allNeighborMessageMultiplication = (1,1)
        for messageKey in self.messages.keys():
            message= self.messages[messageKey]
            allNeighborMessageMultiplication = \
                (allNeighborMessageMultiplication[PRODUCT_TYPE_BAD]*message[PRODUCT_TYPE_BAD] , \
                 allNeighborMessageMultiplication[PRODUCT_TYPE_GOOD]*message[PRODUCT_TYPE_GOOD])
        normalizingValue = (self.score[PRODUCT_TYPE_BAD]*allNeighborMessageMultiplication[PRODUCT_TYPE_BAD])+ \
                (self.score[PRODUCT_TYPE_GOOD]*allNeighborMessageMultiplication[PRODUCT_TYPE_GOOD])
        self.score = ((self.score[PRODUCT_TYPE_BAD]*allNeighborMessageMultiplication[PRODUCT_TYPE_BAD])/normalizingValue,\
                (self.score[PRODUCT_TYPE_GOOD]*allNeighborMessageMultiplication[PRODUCT_TYPE_GOOD])/normalizingValue)

class review(SIALink):
    def __init__(self, _id, usrId, bnId, rating, timeOfReview, txt='', recommended=True):
        super(review, self).__init__()
        self.id = _id
        self.rating = rating
        self.usrId = usrId
        self.bnId = bnId
        self.timeOfReview = timeOfReview
        self.text = txt
        self.recommended = recommended

    def getRating(self):
        return self.rating

    def getId(self):
        return self.id

    def getReviewSentiment(self):
        if self.getRating()>3.0:
            return REVIEW_TYPE_POSITIVE
        elif self.getRating()<3.0:
            return REVIEW_TYPE_NEGATIVE
        else:
            return REVIEW_TYPE_NEUTRAL

    def getUserId(self):
        return self.usrId

    def getBusinessID(self):
        return self.bnId

    def getTimeOfReview(self):
        return self.timeOfReview

    def getReviewText(self):
        return self.text

    def setReviewText(self, txt):
        self.text = txt

    def isRecommended(self):
        return self.recommended

    def calculateBeliefVals(self, user, business):
        self.score = user.getMessageFromNeighbor(business)

    def toString(self):
        return 'Review by Usr:'+self.usrId+ ' on Bnss:'+ self.bnId+' Rating:'+str(self.rating)+' Review Time:'+\
               str(getDateForReview(self))+' Review Comment:'+ str(self.getReviewText())


def getDateForReview(r):
    review_date = ''
    if isinstance(r.getTimeOfReview(), datetime):
        return r.getTimeOfReview().date()

    if isinstance(r.getTimeOfReview(), date):
        return r.getTimeOfReview()

    if '-' in r.getTimeOfReview():
        review_date = re.split('-', r.getTimeOfReview())
        review_date =  date(int(review_date[0]), int(review_date[1]), int(review_date[2]))
    else:
        review_date = re.split('/', r.getTimeOfReview())
        review_date = date(int(review_date[2].strip('\\')), int(review_date[0].strip('\\')), int(review_date[1].strip('\\')))
    return review_date


init_COMP_POT()