import sys
import random
import math
import copy
from collections import defaultdict
from entry import Entry 
from node import Node
from rule import Rule
from precondition import Precondition

class C45:

	def isdigitnegative(toTest):
		if isinstance(toTest,str):
			if len(toTest) > 1:
				if toTest[0] == '-' and str(int(float(toTest[1:]))).isdigit():
					return -1 * eval(toTest[1:])
		return toTest

	def getWeight(self, S):
		weight = 0.0
		for entry in S:
			weight += entry.weight
		return weight

	#S: set of instances to filter into subsets
	#a: the attribute for which we want to create subsets of S
	#v: the specific value of attribute a for which we want to create a subset
	#return:
	#Sv: the subset of S where either the value of attribute a is v ,or attribute a is    
	#missing (for which a partial count/weight is assigned to the instance)
	def filterInstances(self, S, a, v):
		Sv = []
		missingValues = []
		n=0
		nv=0
		for entry in S:   
			if entry.attribute[a] != "?":
				n+=1
				if entry.attribute[a] == v:
					nv+=1
					Sv.append(entry)
			else:
				missingValues.append(entry)
		if n > 0:
			partialCount = nv / n
			for entry in missingValues:
				instm = Entry(entry.label)
				for attr in entry.attribute.keys():
					if attr == a:
						instm.setAttribute(a,v)
					else:
						instm.setAttribute(attr, entry.attribute[attr])
				instm.weight *= (partialCount * entry.weight)
				Sv.append(instm)
		return Sv

	#S: set of instances to filter into subsets
	#a: the attribute for which we want to create subsets of S
	#T: threshold
	#Sign: > or <=
	def filterInstancesContinuousThreshold(self, S, a, T, sign):
		Sv = []
		missingValues = []
		n=0
		nv=0
		for entry in S:
			if entry.attribute[a] != "?":
				n+=1
				if sign == ">":
					if entry.attribute[a] > T:
						nv+=1
						Sv.append(entry)
				elif sign == "<=":
					if entry.attribute[a] <= T:
						nv+=1
						Sv.append(entry)
			else:
				missingValues.append(entry)
		if n != 0:
			partialCount = nv / n
			for entry in missingValues:
				newX = copy.deepcopy(entry)
				for attribute in entry.attribute.keys():
					if attribute == a:
						newX.setAttribute(a,T)
					else:
						newX.setAttribute(attribute, entry.attribute[attribute])
				newX.weight *= partialCount
				Sv.append(newX)
		return Sv
				
	#S: data set
	#a: attribute
	#values: possible values
	def splitInformation(self, S, a, values):    
		entropy = 0.0
		for value in values:
			Sv = self.filterInstances(S, a, value)
			if self.getWeight(S) != 0:
				p = self.getWeight(Sv) / self.getWeight(S)
			else:
				p = 0
			if p != 0:
				entropy -= p * math.log(p,2)
		return entropy

	#S: set of instances to filter into subsets
	#a: the attribute for which we want to create subsets of S
	#T: threshold
	def splitInformationContinuous(self, S, a, T):
		entropy = 0.0
		S1 = self.filterInstancesContinuousThreshold(S, a, T, "<=")
		p1 = self.getWeight(S1) / len(S)
		if p1 != 0:
			entropy -= p1 * math.log(p1,2)
		S2 = self.filterInstancesContinuousThreshold(S, a, T, ">")
		p2= self.getWeight(S2) / len(S)    
		if p2 != 0:
			entropy -= p2 *math.log(p2,2)
		return entropy
				
	#S: set of instances to filter into subsets
	#a: the attribute for which we want to create subsets of S
	#values: possible attribute values
	def calculateGain(self, S, a, values):
		#get entropy
		entropy = self.getEntropy(S)
		for value in values:
			Sv = self.filterInstances(S, a, value)
			entropy -= self.getWeight(Sv) / self.getWeight(S) * self.getEntropy(Sv)
		return entropy

	#S: set of instances to filter into subsets
	#a: the attribute for which we want to create subsets of S
	#T: threshold
	def calculateContinuousGain(self, S, a, T):
		try:
			gain = self.continuousGains[tuple(S)][a]
		except:
			if T == 0:
				return 0
			S1 = self.filterInstancesContinuousThreshold(S, a, T, "<=")
			p1 = self.getWeight(S1) / len(S)
			S2 = self.filterInstancesContinuousThreshold(S, a, T, ">")
			p2 = self.getWeight(S2) / len(S)
			self.continuousGains[tuple(S)][a] = self.getEntropy(S) - (p1 * self.getEntropy(S1) + p2 * self.getEntropy(S2))
			gain = self.continuousGains[tuple(S)][a]
		return gain
			
	#S: data set
	def getEntropy(self, S):
		getEntropy = 0.0
		sigma = {}
		for entry in S:
			if entry.label in sigma.keys():
				sigma[entry.label] += entry.weight
			else:
				sigma[entry.label] = entry.weight
		for key in sigma.keys():
			if self.getWeight(S) != 0:
				p = float(sigma[key]) / self.getWeight(S)
			else: 
				p = 0
			if p != 0:
				getEntropy -= p * math.log(p,2)
		return getEntropy

	#S: data set
	#a: attribute
	def calculateThreshold(self, S,a):
		sorted = []
		for entry in S:
			if entry.attribute[a] != "?": # and not entry.attribute[a].isspace(): 
				value = isdigitnegative(entry.attribute[a])
				label = entry.label
				sorted.append((label,value))
		print(sorted)
		sorted.sort(key=lambda tup: tup[1],reverse=False)
		thresholds=[]

		for i in range(0,len(sorted)-1):
			if sorted[i][0] != sorted[i+1][0]: 
				if sorted[i][1] != sorted[i+1][1]:
					threshold= (float(sorted[i][1]) + float(sorted[i+1][1]))/2
					thresholds.append(threshold)
		calculateGain=[(0,0)] #if there are no possible Thresholds we will return 0
		for T in thresholds:
			calculateGain.append((T,self.calculateContinuousGain(S,a,T))) #give calculateGain for each one to determine best 
		calculateGain.sort(key=lambda tup: tup[1],reverse=True)
		if len(calculateGain) == 0:
			if len(sorted) == 0:
				return 0
			return (sorted[len(sorted)-1][1] + sorted[0][1])/2
		return calculateGain[0][0]

	#finds the most common label in S
	def getCommonLabel(self, S):
		commonList = []
		for inst in S:
			found = 0
			for i in range(0, len(commonList)):
				if commonList[i][0] == inst.label:
					commonList[i][1]+=1
					found = 1
			if found == 0:
				commonList.append([inst.label, 1])
		commonList.sort(key=lambda tup: tup[1], reverse=True)
		return commonList[0][0]

	#finds if all instances in S have the same label
	def isHeterogeneous(self, S):
		label = S[0].label
		for inst in S:
			if inst.label != label:
				return False
		return True

	#c45 is called recursively
	def c45(self, S, V, A):
		N = Node()
		if len(A) == 0 or self.isHeterogeneous(S):
			N.addLabel(self.getCommonLabel(S))
			return N
		else:
			bestAttributes = []
			attributeThresholds = {} #keys will be attributes, value will be thresholds
			for a in A:
				values = V[a]
				continuous = False
				for value in values:
					try: 
						try:
							int(isdigitnegative(value))
							continuous = True
						except:
							pass
					except:
						pass
					break
				if continuous != True: #use the normal functions
					splits = self.splitInformation(S, a, values)
					if splits == 0:
						bestAttributes.append((a,0))
					else:
						bestAttributes.append((a,self.calculateGain(S, a, values)/splits))
				else: #use the continuous functions
					T = self.calculateThreshold(S,a)
					splits = self.splitInformationContinuous(S,a,T)
					if splits == 0:
						bestAttributes.append((a,0))
					else:
						bestAttributes.append((a,self.calculateContinuousGain(S,a,T)/splits))
					attributeThresholds[a] = T 
						   
			bestAttributes.sort(key=lambda tup: tup[1], reverse=True)
			aStar = bestAttributes[0][0]
			aVals = V[aStar] 

			if bestAttributes[0][1] == 0: #if calculateGain of aStar is 0
				N.addLabel(self.getCommonLabel(S))
				return N
			N.setAttribute(aStar)
			if aStar in attributeThresholds.keys(): #will determine if aStar has continuous values
				aVals = ["<=", ">"]
				N.setThreshold(attributeThresholds[aStar])
				N.setDistance(S,"Continuous")
			else:
				N.setDistance(S,"Nominal")
			N.addChildren(aVals) #children created here are empty nodes
			for value in aVals:
				Sv = []
				if aStar in attributeThresholds.keys(): #test if continuous
					if value == "<=":
						Sv = self.filterInstancesContinuousThreshold(S,aStar,N.threshold, "<=")
					else:
						Sv = self.filterInstancesContinuousThreshold(S,aStar,N.threshold, ">")
				else:
					Sv =  self.filterInstances(S, aStar, value)
				if len(Sv) == 0:
					mcl = self.getCommonLabel(S)
					N.children[value].label = mcl
				else:
					if aStar not in attributeThresholds.keys():
						newAttributes = []
						for a in A:
							if a != aStar:
								newAttributes.append(a)
						N.children[value] = self.c45(Sv, V, newAttributes)
					else: #if continuous we do not take aStar out of A
						N.children[value] = self.c45(Sv,V,A)
			return N

	#recursively updates the dictionary votes
	#labels are keys and votes are value from dictionary
	#x is the instance we want to predict a  label for
	#root is the root node of the tree
	#votes is the map where we are storing the votes for each possible label
	def findVotes(self, x, root, votes):
		#add the partial weight of x as a vote in votes
		if root.isLeaf():
			votes[root.label]+=x.weight
			return votes
		else:
			val = x.attribute[root.attribute]
			#check if x is missing the node's attribute
			if val == "?":
				for value in root.children.keys():
					if value not in root.distance.keys():
						continue
					valWeight = x.weight * root.distance[value]
					votes = self.findVotes(x, root.children[value], votes)
			elif root.threshold != None:
				child = root.findChildContinuous(val)
				self.findVotes(x, child, votes)
			else:
				self.findVotes(x, root.children[val], votes)
			return votes

	#x is the instance we want to predict a label for
	#root is the root node of the tree
	#return:
	#prediction: the predicted label for x
	def predictNoPrune(self, x, root, labels):
			votes = {}
			for label in labels:
				votes[label] = 0
			votes = self.findVotes(x, root, votes)
			prediction = ""
			#find the label with the highest vote
			maxVotes = 0
			for k,v in votes.items():
				if v > maxVotes:
					prediction = k
					maxVotes  = v
			#predict the label with the highest vote
			return prediction

	def predict(self, x, rules, root, labels, values):
		for rule in rules:
			#print(rule.preconditions)
			for precondition in rule.preconditions:
				match = True
				for key, value in x.attribute.items():
					#print(key + " | " + precondition.attribute)
					if key == precondition.attribute:
						if value == "?":
							print("Value is missing, just like my sanity. :'(")
						if value != precondition.value:
							match = False
							break
				if match:
					return rule.label

	# N = node currently traversing to build the rules
	# preconditions = the list of attribute/value pairs along the current path from the root of the tree to a leaf
	# rules = the list in which we save the rules for each leaf
	def formRules(self, N, preconditions, rules):
		if N.isLeaf(): # if n is a leaf, create a new rule
			newRule = Rule(N.label, preconditions)
			rules.append(newRule)
		elif N.attributeType == "Continuous":
			# handling the '<= root' branch in the tree
			newPreconditionsLess = copy.deepcopy(preconditions)
			
			# Passing in attribute, value, and known ratio (numKnown_<=T / numKnown)
			preLessRoot = Precondition(N.attribute, N.threshold, (N.distance["<="] / N.total))
			
			newPreconditionsLess.append(preLessRoot)
			self.formRules(N.children["<="], newPreconditionsLess, rules) # Recurse until we hit leaf

			newPreconditionsMore = copy.deepcopy(newPreconditionsLess)
			
			# Passing in attribute, value, and known ratio (numKnown_>T / numKnown)
			preMoreRoot = Precondition(N.attribute, N.threshold, (N.distance[">"] / N.total))

			newPreconditionsMore.append(preMoreRoot)
			self.formRules(N.children[">"], newPreconditionsMore, rules) # Recurse until we hit leaf
		else:
			for value, child in N.children.items():
				newPreconditions = copy.deepcopy(preconditions)
				if child.total == 0:
					pre = Precondition(N.attribute, value, 0)
				else:
					pre = Precondition(N.attribute, value, (child.sameAttributes / child.total))
				# pre.setKnownRatio(N.numKnown_v / N.numKnown)
				newPreconditions.append(pre)

				self.formRules(child, newPreconditions, rules) # Recurse until we hit a leaf


	# Creates a list of alternative rules by removing each precondition separately
	# rules = set of rules to manipulate
	def createAlternatives(self, rules):
		alternativeRules = []
		for i in range(len(rules.preconditions)):
			alternativePreconditions = []
			for j in range(len(rules.preconditions)):
				if i != j:
					alternativePreconditions.append(rules.preconditions[j])
			alternativeRule = Rule(rules.label, alternativePreconditions)
			alternativeRules.append(alternativeRule)
		return alternativeRules

	def calculateAccuracy(self, rules, validate):
		total = 0
		correct = 0

		for entry in validate:
			matches = 0
			for precondition in rules.preconditions:
				match = True
				for key, value in entry.attribute.items(): # Optimize here
					if key == precondition.attribute:
						if value != precondition.value:
							match = False
							break
				if match:
					total += 1
					if rules.label == entry.label:
						correct += 1
		if total != 0:
			accuracy = correct / total
		else:
			accuracy = 0
		#print(accuracy)
		return accuracy


	# rules = the set of rules from the tree learned by C4.5
	# valid = the validation set of instances
	def prune(self, rules,validate): # Train data no vlaidate
		#print("\n".join([r.label + " | " + "".join([str(x) for x in r.preconditions]) for r in rules]))
		#print("##################################################################")

		ruleStack = rules
		finalRules = []
		while len(ruleStack) > 0:
			#print(len(ruleStack))
			r = ruleStack.pop(len(ruleStack)-1)
			if r.accuracy < 0:
					r.setAccuracy(self.calculateAccuracy(r, validate))
			#print(r.label + " | " + "".join([str(x) for x in r.preconditions]))
			if len(r.preconditions) == 1:
				finalRules.append(r)
			else:
				alternativeRules = self.createAlternatives(r)
				bestRule = r
				for alternativeRule in alternativeRules:
					if alternativeRule.accuracy < 0:
						alternativeRule.setAccuracy(self.calculateAccuracy(alternativeRule, validate))
					if alternativeRule.accuracy > bestRule.accuracy: # Compare lower bound of confidence intervals, keep track of # of instances each rule matches, when calculating accurac y, also save total var LB = acc - 1.96 sqrt((acc * 1-acc)/totalaka matches)
						bestRule = alternativeRule
				if bestRule == r:
					finalRules.append(r)
				else:
					ruleStack.append(bestRule)

		finalRules.sort(key=lambda x: x.accuracy, reverse=True)
		#print("\n".join([r.label + " | " + str(r.accuracy) + "|" + "".join([str(x) for x in r.preconditions]) for r in finalRules]))
		return finalRules

	def fit(self, test, labels, outputname):
		labelsList = list(labels)
		confusionMatrix=defaultdict(dict)
		for i in range(len(labelsList)):
			for j in range(len(labelsList)):
				confusionMatrix[labelsList[i]][labelsList[j]]=0
		confusionMatrixDict=dict(confusionMatrix)
		for entry in test:
			prediction = self.predict(entry, self.finalRules, self.root, labels, self.values)
			confusionMatrixDict[entry.label][prediction] += 1


		correct = 0
		total = 0
		with open(outputname, 'w') as f:
			for i in range(len(labelsList)):
				f.write(labelsList[i]+",")
			f.write("\n")
			for i in range(len(labelsList)):
				for j in range(len(labelsList)):
					f.write(str(confusionMatrixDict[labelsList[i]][labelsList[j]])+",")
					if i == j:
						correct += confusionMatrixDict[labelsList[i]][labelsList[j]]
					total += confusionMatrixDict[labelsList[i]][labelsList[j]]

				f.write(labelsList[i]+",")
				f.write("\n")
		f.close()
		print(str(correct / total))


		return confusionMatrixDict

	def __init__(self, train, values, attributes, validate, prunePercentage):
		self.train = train
		self.attributes = attributes
		self.values = values
		self.prunePercentage = prunePercentage
		self.continuousGains = defaultdict(dict)
		self.root = self.c45(train, values, attributes)
		rules = []
		self.formRules(self.root, [], rules)
		self.finalRules = self.prune(rules, validate)


		
