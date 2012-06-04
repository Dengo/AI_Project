'''
Holly French and Alexandra Price
Functions to make and display decision trees, and compute accuracy.

The titanic dataset takes a long time due to calculating accuracy with loocv.
Also this requires having Graphviz installed. Also, not sure this works on Windows.
'''
import sys, math, heapq, os, math
from scipy.stats import chi2
from numericTreeClass import *

#import makeHaikuTable

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
            print "p", p
            print "n", n
            delta = 0
            for leaf in node.getChildren():
                print "name and val  ", leaf.getName(), leaf.getValue()
                pk = leaf.getNumYes()
                nk = leaf.getNumNo()
                print "pk", pk
                print "nk", nk
                pHat = getPHat(p, n, pk, nk)
                nHat = getNHat(p, n, pk, nk)
                print nHat, 'nhat'
                if nHat == 0.0:
                    nHat = 0.0000000000001
                if pHat == 0.0:
                    pHat = 0.0000000000001
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
    return tree

def findBestSplitNum(numericData):
    '''
    This finds the best index to split the numeric data in a node on in order to maximize info gain.
    UNTESTED.
    '''
    numericData.sort() #hopefully this sorts by the first value in a list?
    possibleSplits = []
    for i in numericData:
        num = int(i[0])
        if num not in possibleSplits:
            possibleSplits.append(num)
    possibleSplits = possibleSplits[:-1]
    bestSplit = None
    maxInfoGain = 0
    for num in possibleSplits:
        lowData = []
        highData = []
        for i in range(len(numericData)):
            if int(numericData[i][0]) <= num:
                lowData.append(numericData[i])
            else:
                highData = numericData[i:]
                break
        info = getInfoGain(lowData, highData)
        if info > maxInfoGain:
            maxInfoGain = info
            bestSplit = num
    return bestSplit

def getInfoGain(low, high):
    '''
    Gets the info gain of a particular split on our numeric data.
    UNTESTED.
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
        #right now this doesn't happen
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
        childNode = Node()
        for i in numericData:
            totalYes +=i[1]
            totalNo +=i[2]
        if totalYes == 0:
            print "passed all yes"
            rootNode.setName("Outcome")
            rootNode.setOutcome("NO")
        elif totalNo == 0:
            print "passed all no"
            rootNode.setName("Outcome")
            rootNode.setOutcome("YES")
        elif len(dataDict) == 1:
            print "passed all one number"
            if totalYes > totalNo:
                rootNode.setOutcome("YES")
            else:
                rootNode.setOutcome("NO")
        else:
            splitNum = findBestSplitNum(numericData)
            assert(splitNum)

            #print "splitNum  :", splitNum
            #print "splitCategory   :", splitVal[1]
            lowData = numericData[:splitNum + 1]
            highData = numericData[splitNum + 1:]
            numericData = [lowData, highData]
            #ok, here we need to take data in splitVal category and split into two groups to maximize info gain

            for value in numericData: #This just look through both splits and makes then child nodes.
                #print "low or high data:  ", value
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
                    print "this node all no", splitNum
                    childNode.setOutcome("NO")
                elif numNo == 0:
                    print "this node all yes", splitNum
                    childNode.setOutcome("YES")

                #<<<<<<< HEAD
                elif entropyHeap == []: #we are out of attributes to split on
                    print "no more attributes", splitNum
                    if numYes > numNo: #pick most common outcome
                        childNode.setOutcome("YES")
                    else:
                        childNode.setOutcome("NO")

                else:
                    #now we remove the attribute we split on from the data
                    '''
                    categoryIndex = examples[0].index(splitVal[1])
                    newExamples = [examples[0][:categoryIndex]+examples[0][(categoryIndex+1)%len(examples[0]):]]
                    for e in examples:
                        newE = e[:categoryIndex]+e[categoryIndex+1 % len(e):]
                        newExamples.append(newE)
                    parentExamples = dataDict[splitVal[1]]
                    makeTreeHelper(childNode, newExamples, parentExamples)
                    '''
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
                    #print "newEs   ", newExamples
                    makeTreeHelper(childNode, newExamples, parentExamples)
    '''=======
            else:
                #now we remove the attribute we split on from the data
                categoryIndex = examples[0].index(splitVal[1])
                newExamples = [examples[0][:categoryIndex]+examples[0][(categoryIndex+1)%len(examples[0]):]]
                
                for e in examples:
                    newE = e[:categoryIndex]+e[categoryIndex+1 % len(e):]
                    newExamples.append(newE)
                parentExamples = dataDict[splitVal[1]]

                updatedParentExamples = []
                if low:
                    for example in parentExamples:
                        print example[0], splitNum, 'compare'
                        if int(example[0]) < int(splitNum):
                            updatedParentExamples.append(example)
                else:
                    for example in parentExamples:
                        if int(example[0]) >= int(splitNum):
                            updatedParentExamples.append(example)
                makeTreeHelper(childNode, newExamples, updatedParentExamples)
    >>>>>>> 4b4fd475dcd3e482ab4b55841bfe5f4886e5c68d'''
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
  

                
def main():
    fileName = sys.argv[1]
    parsedFile = parseFile(fileName)
    treeTimes = makeTree(parsedFile)
    print "TREE:  "
    treeTimes.printTree()
    '''<<<<<<< HEAD'''
    #chiSquarePruning(treeTimes)
    '''=======
    chiSquarePruning(treeTimes)

    #enter a very hacky section of code.... i did it to test the poem rater
    haikuDict = makeHaikuTable.parseHaiku("individualHaiku")
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

    #wordDict = makeDictionary("wordDict.txt")
    # haiku = {"nouns":3, "verbs":3, "adjectives":4, "avgwordlength":0,"avgsyllables":2}
    print "Is your poem any good?", treeTimes.search(haikuDict)
    >>>>>>> 4b4fd475dcd3e482ab4b55841bfe5f4886e5c68d'''
    #treeTimes.makeGraphViz(looCV(parsedFile))
    treeTimes.makeGraphViz(.5)
    os.system("dot -Tpdf tree.dot -o tree.pdf")
    os.system("open tree.pdf")
    
main()
    
    
