'''
@author: santhosh
'''

from datetime import datetime
import os, pickle

from util import StatConstants
from util import StatUtil
from util import SIAUtil
from util import GraphUtil

def extractStatisticsForMultipleBnss(bnss_list, cross_time_graphs, plotDir, timeLength,
                                     measuresToBeExtracted = StatConstants.MEASURES):
    beforeStat = datetime.now()
    statistics_for_current_bnss = dict()
    superGraph = GraphUtil.SuperGraph()
    bnss_set = set(bnss_list)
    total_time_slots = len(cross_time_graphs.keys())
    for timeKey in cross_time_graphs:
        G = cross_time_graphs[timeKey]
        for reviewId in G.getReviewIds():
            revw = G.getReviewFromReviewId(reviewId)
            usr = G.getUser(revw.getUserId())
            bnss = G.getBusiness(revw.getBusinessID())
            superGraph.addNodesAndEdge(usr, bnss, revw)

        bnss_keys_in_current_time_stamp = G.getBusinessIds()

        for bnssKey in bnss_keys_in_current_time_stamp:
            if bnssKey in bnss_set:
                bnss_file_name = os.path.join(os.path.join(plotDir, 'stats'), bnssKey)
                if not os.path.exists(bnss_file_name):
                    statistics_for_current_bnss[StatConstants.BNSS_ID] = bnssKey
                    statistics_for_current_bnss[StatConstants.FIRST_TIME_KEY] = timeKey
                    statistics_for_current_bnss[StatConstants.FIRST_DATE_TIME] = G.getDateTime()
                else:
                    statistics_for_current_bnss = pickle.load(open(bnss_file_name))

                statistics_for_current_bnss[StatConstants.LAST_TIME_KEY] = timeKey
                statistics_for_current_bnss[StatConstants.LAST_DATE_TIME] = G.getDateTime()

                neighboring_usr_nodes = G.neighbors((bnssKey, SIAUtil.PRODUCT))
                reviews_for_bnss = [G.getReview(usrId, bnssKey) for (usrId, usr_type) in neighboring_usr_nodes]
                ratings = [review.getRating() for review in reviews_for_bnss]

                noOfReviews = -1
                if StatConstants.NO_OF_REVIEWS in measuresToBeExtracted:
                    noOfReviews = StatUtil.calculateNoOfReviews(statistics_for_current_bnss,
                                                                neighboring_usr_nodes, timeKey, total_time_slots)

                if StatConstants.NO_OF_POSITIVE_REVIEWS in measuresToBeExtracted \
                        and StatConstants.NO_OF_NEGATIVE_REVIEWS in measuresToBeExtracted:
                    StatUtil.calculateNoOfPositiveAndNegativeReviews(G, statistics_for_current_bnss, \
                                                                     neighboring_usr_nodes, timeKey, total_time_slots)

                #Average Rating
                if StatConstants.AVERAGE_RATING in measuresToBeExtracted:
                    StatUtil.calculateAvgRating(statistics_for_current_bnss, ratings, timeKey, total_time_slots)

                #Rating Entropy
                if StatConstants.RATING_ENTROPY in measuresToBeExtracted:
                    StatUtil.calculateRatingEntropy(statistics_for_current_bnss,
                                                    ratings, reviews_for_bnss, timeKey, total_time_slots)

                #Ratio of Singletons
                if StatConstants.RATIO_OF_SINGLETONS in measuresToBeExtracted:
                    StatUtil.calculateRatioOfSingletons(statistics_for_current_bnss,
                                                        neighboring_usr_nodes, reviews_for_bnss, superGraph, \
                                                        timeKey, total_time_slots)

                #Ratio of First Timers
                if StatConstants.RATIO_OF_FIRST_TIMERS in measuresToBeExtracted:
                    StatUtil.calculateRatioOfFirstTimers(G, statistics_for_current_bnss, neighboring_usr_nodes,
                                                         reviews_for_bnss, superGraph, \
                                                         timeKey, total_time_slots)

                #Youth Score
                if StatConstants.YOUTH_SCORE in measuresToBeExtracted:
                    StatUtil.calculateYouthScore(G, statistics_for_current_bnss, neighboring_usr_nodes,
                                                 superGraph, timeKey,
                                                 total_time_slots)

                #Entropy Score
                if StatConstants.ENTROPY_SCORE in measuresToBeExtracted:
                    StatUtil.calculateTemporalEntropyScore(G, statistics_for_current_bnss,
                                                           neighboring_usr_nodes, noOfReviews, timeKey,
                                                           timeLength, total_time_slots)

                # Max Text Similarity
                if StatConstants.MAX_TEXT_SIMILARITY in measuresToBeExtracted:
                    StatUtil.calculateMaxTextSimilarity(G, statistics_for_current_bnss,
                                                        neighboring_usr_nodes, noOfReviews, timeKey,
                                                        timeLength, total_time_slots)

                # TOP TF IDF
                if StatConstants.TF_IDF in measuresToBeExtracted:
                    top_tf_idf_word = StatUtil.calculateTopTFIDF(G, statistics_for_current_bnss,
                                                                 neighboring_usr_nodes, noOfReviews,
                                                                 timeKey, total_time_slots)
                # Serialize the the current business
                with open(bnss_file_name, 'w') as f:
                    pickle.dump(statistics_for_current_bnss, f)

    for bnssKey in bnss_set:
        bnss_file_name = os.path.join(os.path.join(plotDir, 'stats'), bnssKey)
        statistics_for_current_bnss = pickle.load(open(bnss_file_name))
        StatUtil.doPostProcessingForStatistics(statistics_for_current_bnss, total_time_slots, measuresToBeExtracted)
        # Serialize the the current business
        with open(bnss_file_name, 'w') as f:
            pickle.dump(statistics_for_current_bnss, f)

    afterStat = datetime.now()
    print 'Stats Generation Time for bnsses:', len(bnss_set), 'in', (afterStat - beforeStat)


def extractBnssStatistics(superGraph, cross_time_graphs, plotDir, bnssKey, timeLength,\
                     measuresToBeExtracted = StatConstants.MEASURES, logStats = False):

    print 'Stats Generation for bnss:', bnssKey
    beforeStat = datetime.now()
    statistics_for_current_bnss = dict()
    statistics_for_current_bnss[StatConstants.BNSS_ID] = bnssKey
    bnssStatFile = None
    if logStats:
        bnssStatFile = open(os.path.join(plotDir,bnssKey+'.stats'),'w')
        bnssStatFile.write('--------------------------------------------------------------------------------------------------------------------\n')
        bnssStatFile.write('Statistics for Bnss:'+bnssKey+'\n')

    total_time_slots = len(cross_time_graphs.keys())
    isInitialized = False
    for timeKey in cross_time_graphs:
        G = cross_time_graphs[timeKey]

        for reviewId in G.getReviewIds():
            revw = G.getReviewFromReviewId(reviewId)
            usr = G.getUser(revw.getUserId())
            bnss = G.getBusiness(revw.getBusinessID())
            superGraph.addNodesAndEdge(usr, bnss, revw)

        if bnssKey in G.getBusinessIds():
            if not isInitialized:
                statistics_for_current_bnss[StatConstants.BNSS_ID] = bnssKey
                statistics_for_current_bnss[StatConstants.FIRST_TIME_KEY] = timeKey
                statistics_for_current_bnss[StatConstants.FIRST_DATE_TIME] = G.getDateTime()
                isInitialized = True
                if logStats:
                    bnssStatFile.write('Business Reviews Started at:'+str(timeKey)+' '+str(G.getDateTime())+'\n')
            statistics_for_current_bnss[StatConstants.LAST_TIME_KEY] = timeKey
            statistics_for_current_bnss[StatConstants.LAST_DATE_TIME] = G.getDateTime()

            if logStats:
                bnssStatFile.write('--------------------------------------------------------------------------------------------------------------------\n')

            neighboring_usr_nodes = G.neighbors((bnssKey, SIAUtil.PRODUCT))
            reviews_for_bnss = [G.getReview(usrId, bnssKey) for (usrId, usr_type) in neighboring_usr_nodes]
            ratings = [review.getRating() for review in reviews_for_bnss]

            if logStats:
                bnssStatFile.write('Reviews in Time Period:'+str(timeKey)+' '+str(G.getDateTime()))
                bnssStatFile.write('\n')
                bnssStatFile.write('Number of reviews:'+str(len(neighboring_usr_nodes)))
                bnssStatFile.write('\n')
                reviews_sorted = sorted(reviews_for_bnss, key=lambda key: SIAUtil.getDateForReview(key))
                for review in reviews_sorted:
                    bnssStatFile.write(review.toString())
                    bnssStatFile.write('\n')

            #No of Reviews
            noOfReviews = -1
            if StatConstants.NO_OF_REVIEWS in measuresToBeExtracted:
                noOfReviews = StatUtil.calculateNoOfReviews(statistics_for_current_bnss, neighboring_usr_nodes, timeKey, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.NO_OF_REVIEWS+':'+\
                                       str(noOfReviews))
                    bnssStatFile.write('\n')
            if StatConstants.NO_OF_POSITIVE_REVIEWS in measuresToBeExtracted \
                    and StatConstants.NO_OF_NEGATIVE_REVIEWS in measuresToBeExtracted:
                StatUtil.calculateNoOfPositiveAndNegativeReviews(G, statistics_for_current_bnss,\
                                                                 neighboring_usr_nodes, timeKey, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.NO_OF_POSITIVE_REVIEWS+':'+ \
                                       str(statistics_for_current_bnss[StatConstants.NO_OF_POSITIVE_REVIEWS]))
                    bnssStatFile.write('\n')
                    bnssStatFile.write(StatConstants.NO_OF_NEGATIVE_REVIEWS+':'+ \
                                       str(statistics_for_current_bnss[StatConstants.NO_OF_NEGATIVE_REVIEWS]))
                    bnssStatFile.write('\n')

            #Average Rating
            if StatConstants.AVERAGE_RATING in measuresToBeExtracted:
                StatUtil.calculateAvgRating(statistics_for_current_bnss, ratings, timeKey, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.AVERAGE_RATING+':'+\
                                       str(statistics_for_current_bnss[StatConstants.AVERAGE_RATING][timeKey]/noOfReviews))
                    bnssStatFile.write('\n')

            #Rating Entropy
            if StatConstants.RATING_ENTROPY in measuresToBeExtracted:
                StatUtil.calculateRatingEntropy(statistics_for_current_bnss, ratings, reviews_for_bnss, timeKey, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.RATING_ENTROPY+':'+\
                                       str(statistics_for_current_bnss[StatConstants.RATING_ENTROPY][timeKey]))
                    bnssStatFile.write('\n')

            #Ratio of Singletons
            if StatConstants.RATIO_OF_SINGLETONS in measuresToBeExtracted:
                StatUtil.calculateRatioOfSingletons(statistics_for_current_bnss, neighboring_usr_nodes, reviews_for_bnss, superGraph,\
                                           timeKey, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.RATIO_OF_SINGLETONS+':'+\
                                       str(statistics_for_current_bnss[StatConstants.RATIO_OF_SINGLETONS][timeKey]))
                    bnssStatFile.write('\n')

            #Ratio of First Timers
            if StatConstants.RATIO_OF_FIRST_TIMERS in measuresToBeExtracted:
                StatUtil.calculateRatioOfFirstTimers(G, statistics_for_current_bnss, neighboring_usr_nodes, reviews_for_bnss, superGraph,\
                                            timeKey, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.RATIO_OF_FIRST_TIMERS+':'+\
                                       str(statistics_for_current_bnss[StatConstants.RATIO_OF_FIRST_TIMERS][timeKey]))
                    bnssStatFile.write('\n')

            #Youth Score
            if StatConstants.YOUTH_SCORE in measuresToBeExtracted:
                StatUtil.calculateYouthScore(G, statistics_for_current_bnss, neighboring_usr_nodes, superGraph, timeKey,
                                    total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.YOUTH_SCORE+':'+\
                                       str(statistics_for_current_bnss[StatConstants.YOUTH_SCORE][timeKey]))
                    bnssStatFile.write('\n')

            #Entropy Score
            if StatConstants.ENTROPY_SCORE in measuresToBeExtracted:
                StatUtil.calculateTemporalEntropyScore(G, statistics_for_current_bnss, neighboring_usr_nodes, noOfReviews, timeKey,
                                              timeLength, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.ENTROPY_SCORE+':'+\
                                       str(statistics_for_current_bnss[StatConstants.ENTROPY_SCORE][timeKey]))
                    bnssStatFile.write('\n')

            # Max Text Similarity
            if StatConstants.MAX_TEXT_SIMILARITY in measuresToBeExtracted:
                StatUtil.calculateMaxTextSimilarity(G, statistics_for_current_bnss, neighboring_usr_nodes, noOfReviews, timeKey,
                                              timeLength, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.MAX_TEXT_SIMILARITY+':'+\
                                       str(statistics_for_current_bnss[StatConstants.MAX_TEXT_SIMILARITY][timeKey]))
                    bnssStatFile.write('\n')

            # TOP TF IDF
            if StatConstants.TF_IDF in measuresToBeExtracted:
                top_tf_idf_word = StatUtil.calculateTopTFIDF(G, statistics_for_current_bnss, neighboring_usr_nodes, noOfReviews, timeKey, total_time_slots)
                if logStats:
                    bnssStatFile.write(StatConstants.TF_IDF+':'+top_tf_idf_word.encode('ascii', 'ignore')+'-'+\
                                       str(statistics_for_current_bnss[StatConstants.TF_IDF][timeKey]))
                    bnssStatFile.write('\n')

                    bnssStatFile.write('--------------------------------------------------------------------------------------------------------------------\n')

    StatUtil.doPostProcessingForStatistics(statistics_for_current_bnss, total_time_slots, measuresToBeExtracted)
    if logStats:
        for measure_key in measuresToBeExtracted:
            bnssStatFile.write(measure_key+':'+\
                                        str(statistics_for_current_bnss[measure_key]))
            bnssStatFile.write('\n')
        bnssStatFile.write('--------------------------------------------------------------------------------------------------------------------\n')
        bnssStatFile.close()

    afterStat = datetime.now()

    print 'Stats Generation Time for bnss:', bnssKey, 'in', afterStat-beforeStat

    return statistics_for_current_bnss