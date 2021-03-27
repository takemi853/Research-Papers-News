#!/usr/bin/env python
# -*- coding: utf-8 -*-
#arXivの最新論文 情報を Notionに投稿＋公開用
# arXiv →このプログラム → Notion
# 210325 追加 子ぺージにabst_jpnを追加し、カードタイルに日本語のアブストラクトを表示できるように
# TODO githubへpush

import os
from notion.client import NotionClient
from notion.block import CollectionViewBlock, TextBlock

import config

# Obtain the `token_v2` value by inspecting your browser cookies on a logged-in (non-guest)
client = NotionClient(token_v2="1514e30defb4a68915bcbcfb4f5a4d65a17e265014af72afd8de21b8198814e99d4caeab077a2af3517c0b5057b4be8624469280439a3c64587b9d46514532d721e5a4c4c9de10ca433ceb7b4bfe")
# client = NotionClient(token_v2=config.TOKEN_V2)
# Replace this URL with the URL of the page you want to edit
#論文リスト のプロジェクトを pageとして設定
# page = client.get_block(config.PAGE_TOKEN)
page = client.get_block("https://www.notion.so/f16ccdddbf42445d918b10ab5fce9e83")
# print("The old title is:", page.title)
page.children #エラー対策(原因不明だがこれがないと invalid input でエラーが起こる)
# Access a database using the URL of the database page or the inline block
# cv = client.get_collection_view(config.DATABASE_TOKEN)
cv = client.get_collection_view("https://www.notion.so/408f30d1232e4c6cb22e0df6852362f0?v=8eaa8e714b394a869c0042f73177893c")

######################
#転送# (翻訳+原文)
import pprint
import arxiv
import pandas as pd
import numpy as np
from numpy.random import *
from tqdm import tqdm
 
from datetime import datetime
import re
import requests
from googletrans import Translator
from time import sleep
 
import arxiv
 # 検索ワード
for i in np.arange(2):
    # category = ["AI","CL","CC","CE","CG","GT","CV","CY","CR","DS",
    category = ["CL","CC","CE","CG","GT","CV","CY","CR","DS",
                "DB","DL","DM","DC","ET","FL","GL","GR","AR","HC",
                "IR","IT","LO","LG","MA","MS","MM","NI","NE","NA",
                "OS","OH","PF","PL","RO","SI","SE","SD","SC","SY"]
    if i==0:
        QUERY = "cs.AI"
    #下4行はカテゴリーをランダム選択したバージョン
    #ここはある程度量のあるものを選択できるように調整するか...
    elif i==1:
        rand_cat = int(rand()*39)
        QUERY = "cs."+ category[rand_cat]
        print(rand_cat,category[rand_cat])

    QUERY = "cs.AI OR cs.CV"
    for i in category:
        QUERY += "OR cs.{}".format(i)

    
#     QUERY = "cs.AI"
    dt = datetime.now().strftime("%Y%m%d")
    dt = str(int(dt)-2)
    # dt=str(20201130) #デバック用(ここは2020というように4桁表示)
    print(str(int(dt)))
    # translator = Translator() 
    # result_list = arxiv.query(query = 'cat:cs.AI AND submittedDate:[20201223000001 TO 20201223235959]',max_results=2)
    result_list = arxiv.query(query = 'cat:{} AND submittedDate:[{}000001 TO {}235959]'.format(QUERY,dt,dt),max_results=50,sort_by='submittedDate')
    # print(result_list[1])
    def translate(text):
        tr = Translator(service_urls=['translate.googleapis.com'])
        while True:
            try:
                text_ja = tr.translate(text,src="en", dest="ja").text
                return text_ja
                break
            except Exception as e:
                tr = Translator(service_urls=['translate.googleapis.com'])


    def translate_post(df):
        title_jpn = translate(title)
        abst_jpn = translate(abst)
        print("-------"+str(count)+"ページ目-------")
        print("author:{}".format(author))
        print(url)
        print("title:{}".format(title_jpn))
        print("date:{}".format(date))
        print("Abstract:{}".format(abst_jpn))
        print("Category:{}".format(cat))
        print(df.iloc[1,1])
        
#notionへの投稿
        row = cv.collection.add_row()
        row.name = title_jpn
        row.author = author
        row.category = cat
        row.url = url
        row.abstract_jp = abst_jpn
        row.abstract = abst
        row.submitted_date = date
        row.children.add_new(TextBlock, title=abst_jpn)

        sleep(20)

    count = 1

    def pickupHotword(doc):
        docs = []
        docs.append(doc)
        df = pd.DataFrame(columns=['category_id', 'name', 'tf-idf'])
        #参考　https://tex2e.github.io/blog/python/tf-idf　より
        #参考：TF-IDFを用いた「Kaggle流行語大賞2020」https://upura.hatenablog.com/entry/2020/12/08/234045
        from sklearn.feature_extraction.text import TfidfVectorizer
        import nltk
        nltk.download('stopwords')
        from nltk.corpus import stopwords


        stopWords = stopwords.words("english")
        stopWordsAdd = ['data', 'devices','device','accuracy', 'ai','model','framework',
                        'without','due','also','base','based'
                        'simple', 'ashrae', 'ieee',
                        'using', 'prediction', 'ml', 'classification', 'regression',
                        'machine', 'learning', 'exercise', 'detection', 'kernel', 'dataset']

        for sw in stopWordsAdd:
            stopWords.append(sw)

        vectorizer = TfidfVectorizer(stop_words=stopWords)
        # vectorizer = TfidfVectorizer(max_df=0.9,ngram_range=(1,5)) # tf-idfの計算
        #                            ^ 文書全体の90%以上で出現する単語は無視する
        X = vectorizer.fit_transform(docs)
        # print('feature_names:', vectorizer.get_feature_names())

        words = vectorizer.get_feature_names()
        for doc_id, vec in zip(range(len(docs)), X.toarray()):
            print('doc_id:', doc_id)
            for w_id, tfidf in sorted(enumerate(vec), key=lambda x: x[1], reverse=True):
                lemma = words[w_id]
                df = df.append({'category_id': doc_id, 'name': lemma, 'tf-idf': round(tfidf,3)}, ignore_index=True)
                # print('\t{0:s}: {1:f}'.format(lemma, tfidf))
        return df



    for result in result_list:
        author = result.author
        url = result.pdf_url
        title = result.title
        date = result.published[0:10]
        abst = result.summary
        cat = result.category

        abst = abst.replace("\n","")
        df = pickupHotword(abst)
        translate_post(df) 
        count += 1

    print("Done")

