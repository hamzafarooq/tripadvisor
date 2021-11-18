#!/usr/bin/env python
# coding: utf-8

# In[1]:


from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

data = pd.read_csv("hotelReviewsInParis__en2020110120201105.csv")
#print(data)
reviews_against_hotels = {}
reviews = []
hotelName = []
word = " Name: hotel_name, dtype: object"
for i in data.hotelName.values:
    s = ""
    for j in range(5, len(i)-len(word)):
                s += str(i[j])
    hotelName.append(s)
for i in data["review_body"]:
    reviews.append(str(i))

#print(reviews[0])    
#print(hotelName[0])

for i in range(0, len(reviews)):
    if hotelName[i] not in reviews_against_hotels:
        reviews_against_hotels[hotelName[i]] = ""
        #print(hotelName[i])
    reviews_against_hotels[hotelName[i]] += " " + reviews[i]

#print(reviews_against_hotels)


# In[2]:


def seperate_doted_words(string):
    
    return string


string1 = seperate_doted_words("string1")
#print(string1)


# In[3]:


hotelNames2 = []
reviews2 = []
for key,value in reviews_against_hotels.items():
    hotelNames2.append(key)
    reviews2.append(value)
print(len(hotelNames2))
print(len(reviews2))


# In[4]:


from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from nltk.corpus import stopwords
import numpy as np
import numpy.linalg as LA

train_set = reviews2.copy() #Documents
user_input = input("Search something about Hotels: ")
test_set = [user_input] #Query
# for quries, we will perform wordtovec to understand the meaning of user entered query
stopWords = stopwords.words('english')

vectorizer = CountVectorizer(stop_words = stopWords)
#print vectorizer
transformer = TfidfTransformer()
#print transformer

trainVectorizerArray = vectorizer.fit_transform(train_set).toarray()
testVectorizerArray = vectorizer.transform(test_set).toarray()
#print 'Fit Vectorizer to train set', trainVectorizerArray
#print 'Transform Vectorizer to test set', testVectorizerArray
cx = lambda a, b : round(np.inner(a, b)/(LA.norm(a)*LA.norm(b)), 3)

cosine_list = []
for vector in trainVectorizerArray:
    #print vector
    for testV in testVectorizerArray:
        #print testV
        cosine = cx(vector, testV)
        cosine_list.append(float(cosine))

dict = {"Hotel_Names" : hotelNames2 , "cosine_values" : cosine_list}
df = pd.DataFrame(dict)
df.sort_values(by=['cosine_values'], inplace=True, ascending=False)
Top_Five_Recommended_Hotels = df['Hotel_Names'].head(5).tolist()
print("\n      TOP FIVE RECOMMENDED HOTELS\n")
for i in range(0, len(Top_Five_Recommended_Hotels)):
    print(str(i+1) + '     ' + str(Top_Five_Recommended_Hotels[i]))


# In[ ]:





# In[ ]:




