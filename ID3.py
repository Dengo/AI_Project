'''
Holly French and Alexandra Price
Functions to make and display decision trees, and compute accuracy.

The titanic dataset takes a long time due to calculating accuracy with loocv.
Also this requires having Graphviz installed. Also, not sure this works on Windows.
'''
import sys, math, heapq, os, math
from scipy.stats import chi2
from numericTreeClass import *
from makeHaikuTable import *

def parseFile(fileName):
    '''
    Reads in the tab-delimited dataset into a list of lists.
    '''
    dataFile = open(fileName)
    data = []
    for line in dataFile:
        line = line.strip()
        line = line.split('\t')
        data.append(line)
    dataFile.close()
    return data

def splitData(data):
    '''
    Takes a list of lists, representing a portion of the data.
    Assumes the first item in the data is the names of all the attributes.

    Creates a dictionary of the following form:
    #the values will now be numerical, rather than categorical
    {attr1:[[value1, numYes, numNo][value2, numYes, numNo]],
    attr2: [[value2, numYes, numNo][value4, numYes, numNo]],
    etc}
    '''
    categoryDict = {}
    firstLine = data[0]
    rest = data[1:]
    for row in rest:
        for i in range(len(row) - 1):
            category = firstLine[i]
            attributeFound = False
            if category not in categoryDict:
                categoryDict[category] = []
            for attribute in categoryDict[category]:
                if row[i] == attribute[0]:
                    if row[-1] == 'yes':
                        attribute[1] += 1
                    if row[-1] == 'no':
                        attribute[2] += 1
                    attributeFound = True
                    break
            if not attributeFound:
                if row[-1] == 'yes':
                    categoryDict[category].append([row[i], 1, 0])
                if row[-1] == 'no':
                    categoryDict[category].append([row[i], 0, 1])
    return categoryDict

def chiSquarePruning(tree):
    #from bottom up
    #check if split statistically significant
    #get rid of if not

    #I use the same notation as the book (pg. 706)
    leaves = tree.getLeafNodes()
    leavesPruned = True
    while leavesPruned:
        leafParents = []
        for leaf in leaves:
            parent = leaf.getParent()
            if parent not in leafParents:
                leafParents.append(parent)
        leavesPruned = False
        for node in leafParents:
            numItems = node.getNumItems()
            df = numItems - 1
            p = node.getNumYes()
            n = node.getNumNo()
            delta = 0
            for leaf in node.getChildren():
                pk = leaf.getNumYes()
                nk = leaf.getNumNo()
                pHat = getPHat(p, n, pk, nk)
                nHat = getNHat(p, n, pk, nk)
                #if nHat == 0.0:
                #    nHat = 0.0000000000001
                #if pHat == 0.0:
                #    pHat = 0.0000000000001
                dev = (((pk - pHat)**2)/float(pHat))+(((nk - nHat)**2)/float(nHat))
                delta += dev
            prob = chi2.cdf(delta, df)
            if prob > .05:
                #we want to prune
                leavesPruned = True
                if p > n:
                    node.setOutcome("YES")
                else:
                    node.setOutcome("NO")
                node.pruneChildren()
        leaves = tree.getLeafNodes()

def getPHat(p, n, pk, nk):
    pHat = p * ((pk+nk)/float(p+n))
    return pHat

def getNHat(p, n, pk, nk):
    nHat = n * ((pk+nk)/float(p+n))
    return nHat

def entropy(q):
    '''
    Calculates entropy for a given boolean event occuring with probability q.
    '''
    if q == 1 or q == 0:
        return 0
    else:
        e = -1 * (q * math.log(q, 2) + (1-q) * math.log((1 - q), 2))
        return e

def calculateEntropy(categoryDict):
    '''
    Takes a dictionary of the form produced by splitData.
    Creates a heap orderded by information gain 
    (popping gives you the item with highest gain).
    Calls the entropy(q) function.
    '''
    entropyHeap = []
    #print categoryDict
    totalYes = 0
    totalNo = 0
    someCategory = categoryDict.keys()[0]
    for attribute in categoryDict[someCategory]:
        totalYes += attribute[1]
        totalNo += attribute[2] 

    for category in categoryDict:
        remainder = 0
        curCategory = categoryDict[category]
        for attribute in curCategory:
            numYes = attribute[1]
            numNo = attribute[2]
            probYes = numYes/float(numYes + numNo)
            probNo = numNo/float(numYes + numNo)
            e = entropy(probYes)
            remainder += e * (numYes + numNo)/float(totalYes + totalNo)

        gain = entropy(totalYes/float(totalYes+totalNo)) - remainder
        heapq.heappush(entropyHeap, [1 - gain, category]) #we do 1-gain because heapq makes a min heap
    return entropyHeap


def calculateConfidence(categoryDict):
    '''
    Takes a dictionary of the form produced by splitData.
    Creates a heap orderded by information gain 
    (popping gives you the item with highest gain).
    Calls the entropy(q) function.
    '''
    confidenceHeap = []
    #print categoryDict
    totalYes = 0
    totalNo = 0
    totalNumYesSquared = 0
    totalOverallAttr = 0
    someCategory = categoryDict.keys()[0]
    for attribute in categoryDict[someCategory]:
        totalOverallAttr += 1
        totalYes += attribute[1]
        totalNo += attribute[2] 

    for category in categoryDict:
        remainder = 0
        curCategory = categoryDict[category]
        for attribute in curCategory:
            numYes = attribute[1]
            numNo = attribute[2]
            probYes = numYes/float(numYes + numNo)
            probNo = numNo/float(numYes + numNo)
            e = entropy(probYes)
            numYesSquared = numYes**2

            totalYes += numYes
            totalNumYesSquared += numYesSquared

        meanFrequencies = totalNumYesSquared / totalOverallAttr
        meanFrequenciesSquared = (totalYes / totalOverallAttr)**2

        sigma = math.sqrt(meanFrequencies - meanFrequenciesSquared)

        #this is just a formula for 95% confidence interval.  1.96 was taking from a random
        #stats table in my stats book :p
        lowerBound = self.meanFrequencies - 1.96*sigma
        upperBound = self.meanFrequencies + 1.96*sigma

        #confidence interval is a tuple of upper and lower bound
        confidence_interval = (lowerBound, upperBound)

        conf_ave = (lowerBound + upperBound) / 2
        heapq.heappush(confidenceHeap, [conf_ave, category]) #we do 1-gain because heapq makes a min heap
    return confidenceHeap



def makeTree(fullData):
    '''
    Given a training set (fullData) this makes a DecisionTree object.
    Follows the ID3 algorithm.
    Calls the recursive makeTreeHelper.
    '''
    dataDict = splitData(fullData)
    #print "DATA:  ", dataDict
    entropyHeap = calculateEntropy(dataDict)
    tree = DecisionTree()
    splitVal = heapq.heappop(entropyHeap) #contains the attribute to split on
    #splitval should be the same, I think this is the right category (like numNouns, etc.)
    rootNode = Node()
    rootNode.setName(splitVal[1])
    tree.setRoot(rootNode)
    numYes = 0
    numNo = 0
    for j in dataDict[splitVal[1]]: 
        numYes += j[1]              
        numNo += j[2]

    if numYes == 0:
        rootNode.setOutcome("NO")
        return tree
    if numNo == 0:
        rootNode.setOutcome("YES")
        return tree
    rootNode.setNumItems(numNo+numYes)
    rootNode.setNumYes(numYes)
    rootNode.setNumNo(numNo)
    makeTreeHelper(tree.getRoot(), fullData, dataDict[rootNode.getName()])
    tree.contract() #this is a super hacky way of getting rid of any nodes which split into two of the same outcomes
    return tree

def findBestSplitNum(numericData):
    '''
    This finds the best index to split the numeric data in a node on in order to maximize info gain.
    UNTESTED.
    '''
    numericData.sort() #isn't working?
    possibleSplits = []
    for i in numericData:
        num = int(i[0])
        if num not in possibleSplits:
            possibleSplits.append(num)
    possibleSplits.sort()
    possibleSplits = possibleSplits[:-1]
    bestSplit = 0
    maxInfoGain = 0
    for num in possibleSplits:
        lowData = []
        highData = []
        for i in range(len(numericData)):
            if int(numericData[i][0]) <= num:
                lowData.append(numericData[i])
            else:
                highData.append(numericData[i])
        info = getInfoGain(lowData, highData)
        if info > maxInfoGain:
            maxInfoGain = info
            bestSplit = num
    return bestSplit

def getInfoGain(low, high):
    '''
    Gets the info gain of a particular split on our numeric data.
    '''
    lowYes = 0
    lowNo = 0
    highYes = 0
    highNo = 0
    for i in low:
        lowYes += i[1]
        lowNo += i[2]
    for i in high:
        highYes += i[1]
        highNo += i[2]
    parentYes = lowYes + highYes
    parentNo = lowNo + highNo
    allData = [low, high]
    remainder = 0
    probLowYes = lowYes/float(lowYes + lowNo)
    probLowNo = lowNo/float(lowYes + lowNo)
    lowE = entropy(probLowYes)
    remainder += lowE * (lowYes + lowNo)/float(parentYes + parentNo)
    probHighYes = highYes/float(highYes + highNo)
    probHighNo = highNo/float(highYes + highNo)
    highE = entropy(probHighYes)
    remainder += highE * (highYes + highNo)/float(parentYes + parentNo)
    gain = entropy(parentYes/float(parentYes+parentNo)) - remainder
    return gain




def makeTreeHelper(rootNode, examples, parentExamples):
    '''
    Recursive helper function for makeTree.
    Closely follows the algorithm as laid out in the textbook.

    changed for numeric data. UNTESTED.
    '''
    
    if len(examples) == 1: #we are out of examples
        parentNumYes = 0
        parentNumNo = 0
        childNode = Node()
        childNode.setParent(rootNode)
        rootNode.addChild(childNode)
        childNode.setValue(rootNode.getValue())
        for row in parentExamples:
            parentNumYes += row[1]
            parentNumNo += row[2]
        if parentNumYes > parentNumNo: #pick most common
            childNode.setOutcome("YES")
        else:
            childNode.setOutcome("NO")
    
    else:
        dataDict = splitData(examples)
        entropyHeap = calculateEntropy(dataDict)
        splitVal = heapq.heappop(entropyHeap) #attribute to split on
        rootNode.setName(splitVal[1])
        numericData = dataDict[splitVal[1]]
        #value[0] is the number
        totalYes = 0
        totalNo = 0

        for i in numericData:
            totalYes +=i[1]
            totalNo +=i[2]
        if totalYes == 0:
            rootNode.setName("Outcome")
            rootNode.setOutcome("YES")
        elif totalNo == 0:
            rootNode.setName("Outcome")
            rootNode.setOutcome("NO")
        elif len(dataDict) == 1:
            if totalYes > totalNo:
                rootNode.setOutcome("YES")
            else:
                rootNode.setOutcome("NO")
        else:
            splitNum = findBestSplitNum(numericData)
            lowData = numericData[:splitNum + 1]
            highData = numericData[splitNum + 1:]
            numericData = [lowData, highData]
            #ok, here we need to take data in splitVal category and split into two groups to maximize info gain

            for value in numericData: #This just look through both splits and makes then child nodes.
                low = False
                high = False
                if value == lowData:
                    low = True
                else:
                    high = True 
                childNode = Node()
                childNode.setParent(rootNode)
                rootNode.addChild(childNode)
                if low:
                    childNode.setValue("<= " + str(splitNum))
                else:
                    childNode.setValue("> " + str(splitNum))
                childNode.setName("Outcome") #will be reset by children if not a leaf node

                numYes = 0
                numNo = 0
                for i in value:
                    numYes += i[1]
                    numNo += i[2]

                childNode.setNumItems(numYes+numNo)
                childNode.setNumYes(numYes)
                childNode.setNumNo(numNo)
                if numYes == 0:
                    #print "this node all no", splitNum
                    childNode.setOutcome("NO")
                elif numNo == 0:
                    #print "this node all yes", splitNum
                    childNode.setOutcome("YES")

                elif entropyHeap == []: #we are out of attributes to split on
                    #print "no more attributes", splitNum
                    if numYes > numNo: #pick most common outcome
                        childNode.setOutcome("YES")
                    else:
                        childNode.setOutcome("NO")

                else:
                    #now we remove the attribute we split on from the data, and only pass on the data corresponding to the split
                    categoryIndex = examples[0].index(splitVal[1])
                    newExamples = [examples[0][:categoryIndex]+examples[0][(categoryIndex+1)%len(examples[0]):]]
                    for e in examples[1:]:
                        if low and int(e[categoryIndex]) <= splitNum:
                            newE = e[:categoryIndex]+e[categoryIndex+1 % len(e):]
                            newExamples.append(newE)
                        if high and int(e[categoryIndex]) > splitNum:
                            newE = e[:categoryIndex]+e[categoryIndex+1 % len(e):]
                            newExamples.append(newE)
                    parentExamples = dataDict[splitVal[1]]
                    makeTreeHelper(childNode, newExamples, parentExamples)
    return
                
def looCV(dataSet):
    '''
    Leave one out cross validation.
    Takes a data set, returns the accuracy of the 
    decisionTree, made using ID3.
    '''
    numCorrect = 0
    numItems = len(dataSet) - 1
    for i in range(1,len(dataSet)):
        testItem = dataSet.pop(i) #the data point we will try to classify
        testTree = makeTree(dataSet)

        #make a dictionary in order to pair the categories and values for the data point
        itemDict = {}
        categories = dataSet[0]
        for i in range(len(categories) - 1):
            itemDict[categories[i]] = testItem[i]

        outcome = testTree.search(itemDict)
        if not outcome: #there was no branch in the decision tree for the specified data point
            numItems -= 1

        elif outcome.lower() == testItem[-1]:
            numCorrect += 1
        dataSet.insert(i, testItem)
    accuracy = numCorrect/float(numItems)
    return accuracy


def activeLearning(treeTimes, parsedFile):
    """
    the active learning algorithm uses confidence intervals to determine which poem the user should rate
    that would be most useful in building a better decision tree
    """
    heap = treeTimes.createConfidenceHeap(parsedFile)
    bestGuess = heapq.heappop(heap)[1]

    #we need to get an unrated haiku from our haikudb here
    unratedPoems = []
    lineNum = 0
    unratedLineNumList = []
    for poem in parsedFile:
        lineNum += 1
        if poem[-1] == None or poem[-1] == "None":
            unratedPoems.append(poem)
            unratedLineNumList.append(lineNum)

    unratedIndex = 0
    haikuDB = open("haikuDB")
    haikuList = []
    for line in haikuDB:
        line = line.split("\t")
        try:
            val = int(line[0])
            haiku = ""
            if val in unratedLineNumList:
                next1 = haikuDB.next()
                next2 = haikuDB.next()
                haiku += line[1] + next1 + next2
                haikuList.append(haiku)
        except ValueError:
            pass

    index = 0
    for individualHaiku in unratedPoems:
        index += 1
        entryDict = {}
        for i in range(len(parsedFile[0])):
            entryDict[parsedFile[0][i]] = individualHaiku[i]
        if treeTimes.isItemInNode(entryDict, bestGuess):
            rating = ""
            while rating != "yes" or rating != "no":
                print 
                print haikuList[index]
                rating = raw_input("Please rate this haiku.  Is it good?  Enter y/n: ")
                #then we need to add this to our rating
                if rating == "y":
                    individualHaiku[-1] = "yes"
                    break
                if rating == "n":
                    individualHaiku[-1] = "no"
                    break
            parsedFile.append(individualHaiku)
            break

def ratePoem():
    individualHaikuFile = raw_input("Please enter a txt file of the haiku you want rated.")
    individualHaiku = open(individualHaikuFile)
    haikuDict = makeHaikuTable.parseHaiku(individualHaiku)
    wordDict = makeHaikuTable.makeDictionary("wordDict.txt")
    haikuFile = makeHaikuTable.makeTableFile(haikuDict, wordDict)
    parsedHaiku = parseFile("haikuTable.txt")
    print parsedHaiku
    haikuDict = {}
    for i in range(len(parsedHaiku[0])):
        item =  parsedHaiku[0][i].strip()
        if item == "av. word length":
            item = "avgwordlength"
        if item == "av. syllables":
            item = "avgsyllables"
        haikuDict[item] = parsedHaiku[1][i]

    print "Is your poem any good?", treeTimes.search(haikuDict)


                    
def main():
    fileName = sys.argv[1]
    parsedFile = parseFile(fileName)
    tree = makeTree(parsedFile)
    chiSquarePruning(tree)
    wordDict = makeDictionary("wordDict.txt")
    #haiku = raw_input("Please type a haiku (all on one line):   \n")
    #haikuInfo = getHaikuInfo(haiku, wordDict)
    #print "Is your poem any good?", tree.search(haikuInfo)
    tree.makeGraphViz(looCV(parsedFile))
    os.system("dot -Tpdf tree.dot -o tree.pdf")
    os.system("open tree.pdf")

    activeLearning(tree, parsedFile)
    
if __name__=="__main__":
    main()
    
    
