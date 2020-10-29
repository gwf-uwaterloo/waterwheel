from pyserini import analysis, index
from pyserini.search import SimpleSearcher
import itertools
import math
import pandas as pd
import json
import os

index_reader = index.IndexReader.from_prebuilt_index('enwiki-paragraphs')
searcher = SimpleSearcher.from_prebuilt_index('enwiki-paragraphs')

N =  searcher.num_docs
i = 0
for term in index_reader.terms():
    ret.append([term.term, math.log(N/term.cf)]) #calculate idf
    i += 1
print('done iterate terms')

df= pd.DataFrame(ret,columns = ['term','idf'])
df_sorted = df.sort_values(by=['idf']) # sort idf from low to high
head = df_sorted.head(3000) #can choose other cutoff
stop_words = head['term'].tolist()
stop_words.sort() #sort by lexcial order 
filtered = [x for x in stop_words if x.isalpha()]
stop = {'stop_words':filtered}

with open(os.path.join('./data'),'stop_word.json', 'w') as outfile:
    json.dump(stop,outfile,indent =2)

