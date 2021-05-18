#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 20:33:51 2021

@author: Viktoria
"""



import pandas as pd
import numpy as np
import os
import chemdataextractor
from chemdataextractor import Document
import spacy
from spacy.tokens import DocBin
from spacy import displacy
import re
from nltk.tokenize import TweetTokenizer
import nltk
from nltk.corpus import stopwords



def main_chemicals():


    main = os.getcwd()
    os.chdir(main)
    
    
    f = open('exercise_experimentals.txt', 'rb')
    doc = Document.from_file(f)
    
    
    
    # ## Question 1. What was added to what?
    
    # ### Step 1. Get the sentences of the text up until the last occurrence of addition. <br> Step 2. Get the named entities that stand for the ingredients. <br> Step 3. Get the syntactic position of the ingredients to find out 'what was added to what'. In 'X was added to Y' X is the subject, Y is the object. 
    
    # In[ ]:
    
    
    #Create a list of strings (recipes) which contains the texts of each recipe up until the last occurrence of the phrase that contains the addition
    
    recipes=[]
    
    for i in range(0, len(doc)):
        
        paragraph=[]
        tracker=[]
        
        for sentence in doc[i].sentences:
            text=str(sentence).lower()
            paragraph.append(text)
            
            #check if the addition phrase is present
            if 'add' in text or 'addition' in text:
                tracker.append(1)
            else:
                tracker.append(0)
                
        #consider the text until the last occurrence of the 'add' phrase
        paragraph = paragraph[0:np.max(np.nonzero(tracker))+1]    
        paragraph = ' '.join([p for p in paragraph])
        recipes.append(paragraph)
    
    
    # In[ ]:
    
    
    #Get a list of all the chemical elements in each recipe
    
    entities=[]
    for i in range(len(doc.cems)):
        entities.append(str(doc.cems[i]).lower())
    
    
    # In[ ]:
    
    
    # Create dictionaries for each recipe (indices) with the name of the entity, starting position, ending position. 
    # These dictionaries will be passed to spacy to get the syntax of the sentences.
    
    tagged_entities = []
    
    for recipe in recipes:
        
        indices={}
        
        #check which entities appear in the text
        for entity in entities:
            
            #look for the entity 
            if entity in recipe:
                
                #get the start & end position and add it to the dict
                start = recipe.index(entity)
                end = recipe.index(entity)+len(entity)
                indices[entity]=start, end
                
        #only match the full chemical name, not if e.g. the word 'h2o' is contained in a longer name
        keys = list(indices.keys())
        for word in keys: 
            if sum(word in k for k in keys) > 1: #more than 1 occurrences 
                indices.pop(word) #pop the short word that is contained by other words
        
        
        tagged_entities.append(indices)
    
    
    # In[ ]:
    
    
    # Add the named entities to spacy, then get the information which one was the subject and which one the object of the sentence
    
    nlp = spacy.load("en_core_web_sm") # load a new spacy model
    
    db = DocBin() # create a DocBin object
    corpora = [] # these will be the syntactically tagged recipes
    
    for i,v in enumerate(recipes):
    
        indices=tagged_entities[i]
    
        spacy_doc = nlp(recipes[i]) # create doc object from text
        ents = []
        
        for (key,value) in indices.items(): # add character indexes
            span = spacy_doc.char_span(value[0], value[1], label=key, alignment_mode="expand")
            
            if span is None:
                print('none')
            else:
                ents.append(span)
              
        spacy_doc.ents = ents # label the text with the ents
        db.add(spacy_doc)
        
        corpora.append(spacy_doc)
    
    
    # In[ ]:
    
    
    #Check on a single recipe if the tagging process was successful
    
    #spacy_doc.has_annotation("TAG") #gives True
    
    
    # In[ ]:
    
    
    #Visualise the sentence structure of a single recipe
    
    #displacy.render(spacy_doc, style="dep")
    
    
    # In[ ]:
    
    
    # Now find out whether the ingredient in the recipe was a subject or an object
    # X was added to Y -> X is the subject, Y is the object
    
    for c in range(len(corpora)):
    
        ingredients={}
        indices = tagged_entities[c]
    
        #get the name and the syntactic position
        for token in corpora[c]:
        
            if 'subj' in token.dep_ or 'obj' in token.dep_:
         
                #if this is a chemical entity we are interested in
                for k in indices.keys():
                    if token.text in k:
                      
                        #add the syntactic information
                        indices[k] = token.dep_
    
    
    # In[ ]:
    
    
    #In a structure "X was added to Y", X is the subject, i.e. the chemical being added & Y is object, i.e. the recipient
    
    def clean_results(value):
        
        if 'subj' in value:
            value = 'added to mixture'
        elif 'obj' in value:
            value = 'recipient'
        else:
            value = 'order of addition unknown'
            
        return value
    
    
    # In[ ]:
    
    
    # Prepare results to Questions 1.
    
    res_1=[]
    
    for i in tagged_entities:
        ingredients = {key:clean_results(value) for (key,value) in i.items()}
        res_1.append(ingredients)
    
    
    # In[ ]:
    
    
    res_1
    
    
    # ## Question 2. How much of each constituent was added?
    
    # ### Quantities are either in brackets after the named entity (0.01 mmol, 4.28 mg), or shortly before it '2 ml dry toluene'
    
    # In[ ]:
    
    
    res2=[]
    
    sw = stopwords.words('english')
    
    #for each recipe
    for i,recipe in enumerate(recipes):
        
        res=[]
        
        #and each ingredient
        for entity in tagged_entities[i].keys():
            
            #look for the information in brackets
            pattern = re.compile(re.escape(entity) + r"\s*\(.*?\)")
            try:
                quant = re.search(pattern, recipe).group()
                res.append(quant)
            
            #tokenize and find the information preceding the entity
            except:
                
                sent = ' '.join([w for w in recipe.split() if w not in sw])
                tokenizer = TweetTokenizer()
                wordlist = tokenizer.tokenize(sent)
                for i,w in enumerate(wordlist):
                    if w in entities:
                        
                        #add the 3 words preceding the named entity
                        res.append(' '.join([wordlist[i-3], wordlist[i-2], wordlist[i-1], wordlist[i]]))
                        
        res2.append(res)
    
    
    # ### Question 3. Type of addition: in portions or continuous?
    
    # In[ ]:
    
    
    #Look for diagnostic phrases that inform us about the type of addition (identified in the data)
    #These will be stored in a text file so that the users of the code can edit these expressions any time
    
    os.chdir(main)
    
    with open('continuous_addition.txt', 'r+') as f:
        cont = f.readlines()  
        cont = [re.sub('\n', '', c.lower()) for c in cont]
        
    with open('addition_in_portion.txt', 'r+') as f:
        por = f.readlines()  
        por = [re.sub('\n', '', p.lower()) for p in por]
    
    
    # In[ ]:
    
    
    pattern = re.compile(re.escape(entity) + r"\s*\(.*?\)")
    
    
    # In[ ]:
    
    
    res3 = []
    
    for i,recipe in enumerate(recipes):
        
        if any(c in recipe for c in cont) and any(p in recipe for p in por):
            res3.append('Recipe ' + str(i+1) + ': Mention of both continuous and in-portion addition')
            
        elif any(c in recipe for c in cont):
            res3.append('Recipe ' + str(i+1) + ': Continuous addition')
            
        elif any(p in recipe for p in por):
            res3.append('Recipe ' + str(i+1) + ': Addition in portions')
            
        else:
            res3.append('Recipe ' + str(i+1) + ': Type of addition unknown')
        
        
        
    
    
    return res3
    
    # In[ ]:
    
    

    
    
    # In[ ]:
    
    
    
    
