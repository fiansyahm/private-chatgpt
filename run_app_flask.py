import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import json
import base64
import time
from flask import Flask, request,Response
from flask_cors import CORS
import io
import matplotlib
from tabulate import tabulate
matplotlib.use('Agg')


application = Flask(__name__)
# CORS(app)

def getData(data=None):
    if data == None:
        table = [
            ["a1", ['a', 'b', 'c'],   ['a', 'b', 'c', 'k', 'l'], '1993', ['p1', 'p2'],'title of a1','nation of p1'], 
            ["a2", ['c', 'd', 'e'],   ['a', 'c', 'd', 'e', 'm', 'n'], '1993', ['p1', 'p3'],'title of a2','nation of p1'],
            ["a3", ['f', 'g', 'h'],   ['c', 'd', 'f', 'g', 'h', 'o'], '1993', ['p2', 'p4', 'p5'],'title of a3','nation of p2'], 
            ["a4", ['i', 'j'],        ['c', 'd', 'p', 'q'], '1994', ['p3', 'p6'], ['a1', 'a2'], 'title of a4', 'nation of p3'], 
            ["a5", ['dj', 'dk'],      ['a', 'dj', 'dk', 'm', 'r'], '1994', ['p1', 'p7'], ['a1', 'a2', 'a3'], 'title of a5','nation of p1'], 
            ["a6", ['d', 'ac', 'ad'], ['d', 'ac', 'ad', 's', 't'], '1994', ['p8', 'p9'], ['a1', 'a3'], 'title of a6','nation of p8'],
        ]
    else:
        table = data
    return (table)

def getArticleIdAuthorReferencesAndAuthor(table):
    time_start = time.time()
    pairs = []
    authors = []
    articles = []
    initial_articles_pair = []
    title_articles_pair = []
    initial_author_pair = []
    nation_author_pair = []

    for i in table:
        row = []
        row.append(i[0])
        articles.append(i[0])
        row.append(i[4])
        count=0
        for penulis in i[4]:
            count+=1
            if count==1:
                initial_author_pair.append(penulis)
                # print("this is my country "+i[len(i)-1])
                nation_author_pair.append(i[len(i)-1])
            authors.append(penulis)
        row.append(i[5])
        for article in i[5]:
            # memastikan article != ''
            if len(article) > 1:
                # print("this is my article "+article)
                articles.append(article)
        pairs.append(row)

        # memasukkan array kode artikel dan judulnya
        initial_articles_pair.append(i[0])
        title_articles_pair.append(i[len(i)-2])
    # menghilangkan duplikat
    authors = sorted(set(authors))
    articles = sorted(set(articles))
    time_end = time.time()
    # print("getArticleIdAuthorReferencesAndAuthor time: ", time_end - time_start)
    return pairs, authors, articles,initial_articles_pair ,title_articles_pair,initial_author_pair,nation_author_pair

def author_matrixs(authors):
    time_start = time.time()
    author_matrix = []
    for author_x in authors:
        for author_y in authors:
            row = []
            row.append(author_x)
            row.append(author_y)
            author_matrix.append(row)
    time_end = time.time()
    # print("author_matrixs time: ", time_end - time_start)
    return author_matrix


# ge table 2 data start
def getTable2Data(pairs, search_matrix, type):
    time_start = time.time()
    # create a DataFrame to store the author matrix
    author_matrixs = []
    for i in search_matrix:
        author_matrixs.append([i[0], i[1], 0])
    
    new_search_matrix = {}
    count = 0
    for i in search_matrix:
        new_search_matrix[i[0]+"-"+i[1]] = count
        count += 1
    
    article_and_authors={}
    for i in pairs:
        article_and_authors[i[0]]=i[1]

    if type == "author":
        for i in pairs:
            penulisList = i[1]
            authorList = i[2]
            for author in authorList:
                if len(author) <= 1:
                    continue
                for penulis in penulisList:
                    # rujukan tidak ada di daftar penulis
                    if article_and_authors.get(author) is None:
                        continue
                    for row in article_and_authors[author]:
                        if penulis != row:
                            author_matrixs[new_search_matrix[penulis+"-"+row]][2] += 1
        print("\n")
    elif type == "article":
        for i in pairs:
            penulisList = i[0]
            authorList = i[2]
            author = penulisList
            for author_reference in authorList:
                # memastikan article/author != ''
                if len(author) <= 1 or len(author_reference) <= 1:
                    continue
                author_matrixs[new_search_matrix[author+"-"+author_reference]][2] += 1

    time_end = time.time()
    # print("getTable2Data time: "+str(time_end-time_start))
    return author_matrixs
# ge table 2 data end

def makeTable2(author_matrix, authors):
    # perluotomasi
    time_start = time.time()

    new_search_matrix = {}
    for i in author_matrix:
        new_search_matrix[i[0]+"-"+i[1]] = i[2]

    pretable2 = []
    for p1 in authors:
        authortmp = []
        for p2 in authors:
            val = new_search_matrix[p2+"-"+p1]
            authortmp.append(val)
        pretable2.append(authortmp)
    # print(pretable2)
    table2 = pd.DataFrame(pretable2, columns=authors, index=authors)
    print("Tabel 2: Only Relational Matrix")
    print(table2)
    time_end = time.time()
    # print("makeTable2 time: "+str(time_end-time_start))
    return table2, pretable2

def getTopAuthor(authors, author_rank, ranking):
    time_start = time.time()
    author_ranking = []
    count = -1
    for author in authors:
        count += 1
        author_ranking.append((author, author_rank[count]))
    sorted_authors = sorted(author_ranking, key=lambda x: x[1], reverse=True)
    # get the top 20 author names
    top_authors = [x[0] for x in sorted_authors[:ranking]]
    time_end = time.time()
    # print("getTopAuthor time: "+str(time_end-time_start))
    return top_authors

def add_node_graph(G, author_matrixs,top_authors,top_authors_and_top_authors_bolean,top_authors_and_common_authors_bolean):
    time_start = time.time()
    for author_matrix in author_matrixs:
        if author_matrix[2] > 0:
            if top_authors_and_top_authors_bolean=="ON" and not (author_matrix[1] in top_authors and author_matrix[0] in top_authors):
                continue
            if top_authors_and_common_authors_bolean=="ON" and not author_matrix[1] in top_authors:
                continue
            # (penulis merujuk,dirujuk,nilai)
            G.add_edge(author_matrix[0],
                       author_matrix[1], weight=author_matrix[2])
            G.add_node(author_matrix[0])
            G.add_node(author_matrix[1])
    time_end = time.time()
    # print("add_node_graph time: "+str(time_end-time_start))
    return G

def get_no_outer_author(authors, author_rank, exist_authors):
    time_start = time.time()
    count = -1
    outer_author_rank = []
    outer_authors = []
    for author in authors:
        count += 1
        if author not in exist_authors:
            outer_author_rank.append(author_rank[count])
            outer_authors.append(author)
            authors.pop(count)
            author_rank.pop(count)
    time_end = time.time()
    # print("get_no_outer_author time: "+str(time_end-time_start))
    return authors, author_rank, outer_author_rank, outer_authors

def makeTermGraph(authors, author_matrixs, author_rank, outer_author, ranking):
    # perluooptimasi
    time_start = time.time()
    # acuan
    count = 0
    search_author_json={}
    for i in authors:
        search_author_json[i]=count
        count+=1

    # nilai author tanpa hubungan ex:0.123
    rank_outer_author = author_rank[len(author_rank)-1]
    # ranking author yang ingin ditampilkan ex:5,10,20
    ranking = ranking
    # pilihan menampilkan author tanpa relasi ex:tampilkan,tidak
    outer_author = int(outer_author)
    # dapatkan list top author ex:['p1','p2','p3']
    top_authors = getTopAuthor(authors, author_rank, ranking)
    # inisilaize graph
    G = nx.Graph()
    # author merujuk & dirujuk
    if outer_author == 2:
        top_authors_and_top_authors_bolean = "ON"
        top_authors_and_common_authors_bolean = "OFF"
    elif outer_author == 3:
        top_authors_and_top_authors_bolean = "OFF"
        top_authors_and_common_authors_bolean = "ON"
    else:
        top_authors_and_top_authors_bolean = "OFF"
        top_authors_and_common_authors_bolean = "OFF"
    G = add_node_graph(G, author_matrixs,top_authors,top_authors_and_top_authors_bolean,top_authors_and_common_authors_bolean)
    # inisiliasisi ukuran node dan warna
    my_node_sizes = []
    my_node_colors = []
    labels = {}

    print("total all author name:"+str(len(authors)))
    print("total all author Rank:"+str(len(author_rank)))

    authors, author_rank, outer_author_rank, outer_authors = get_no_outer_author(
        authors, author_rank, G.nodes)
    
    search_authors={}
    count=0
    for author in authors:
        search_authors[author]=count
        count+=1

    print("total relational author name:"+str(len(authors)))
    print("total relational author Rank:"+str(len(author_rank)))

    # default=125
    if outer_author == 0:
        total_author = len(G.nodes) + len(outer_authors)
    else:
        total_author = len(G.nodes)
    print("total author:"+str(total_author))

    if 0<=total_author<=200:
        subplot_size=25
        k=2
        authors_node_size_x=5000
        outer_author_node_size_1=2000
        outer_author_node_size_2=1000
        node_labels_font_size=25
        edge_labels_font_size=20

    if 200<total_author<=400:
        subplot_size=25
        k=2
        authors_node_size_x=5000
        outer_author_node_size_1=2000
        outer_author_node_size_2=1000
        node_labels_font_size=25
        edge_labels_font_size=20
    
    if 400<total_author<=600:
        subplot_size=30
        k=2.5
        authors_node_size_x=1600
        outer_author_node_size_1=2000
        outer_author_node_size_2=200
        node_labels_font_size=25
        edge_labels_font_size=8

    elif 600<total_author:
        subplot_size=32
        k=3.2
        authors_node_size_x=800
        outer_author_node_size_1=1000
        outer_author_node_size_2=100
        node_labels_font_size=15
        edge_labels_font_size=5
    else:
        subplot_size=25
        k=2
        authors_node_size_x=5000
        outer_author_node_size_1=2000
        outer_author_node_size_2=1000
        node_labels_font_size=25
        edge_labels_font_size=20

    for author in G.nodes:
        size = author_rank[search_authors[author]]
        if size > rank_outer_author:
            # jika iya nilainya *300
            my_node_sizes.append(size * authors_node_size_x)
            if author in top_authors:
                my_node_colors.append('black')
            else:
                my_node_colors.append('blue')
        else:
            # jika tidak dirujuk nilainya 10
            my_node_sizes.append(outer_author_node_size_1)
            my_node_colors.append('red')
        labels[author] = str(search_author_json[author])

    if outer_author == 0:
        for author, size in zip(outer_authors, outer_author_rank):
            G.add_node(author)
            my_node_sizes.append(outer_author_node_size_2)
            my_node_colors.append('red')
            labels[author] = str(search_author_json[author])

    # Set the maximum number of open figures before showing a warning
    plt.rcParams['figure.max_open_warning'] = 20

    # Close all open figures before creating a new one
    plt.close('all')
    fig, ax = plt.subplots(figsize=(subplot_size, subplot_size))
    # decrease k parameter to increase spacing between nodes
    pos = nx.spring_layout(G, seed=7, k=k)
    nx.draw_networkx_nodes(G, pos, alpha=0.7,
                           node_size=my_node_sizes,
                           node_color=my_node_colors
                           )  # increase node size to 200
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(),
                           width=1, alpha=0.5, edge_color="green")
    nx.draw_networkx_labels(G, pos, font_size=node_labels_font_size,
                            font_family="sans-serif", font_color="white",
                            labels=labels
                            )

    edge_labels = nx.get_edge_attributes(G, name='weight')

    edge_labels = {(u, v): weight_matrix for u, v,
                   weight_matrix in G.edges(data='weight')}
    
    draw_time=time.time()
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=edge_labels_font_size)
    end_draw_time=time.time()-draw_time
    # print("draw time: "+str(end_draw_time))


    buf = io.BytesIO()


    plt_time=time.time()
    plt.savefig(buf, format='png')
    end_plt_time=time.time()-plt_time
    # print("plt time: "+str(end_plt_time))

    output = buf
    output.seek(0)


    # my_base64_jpgData = base64.b64encode(output.read())
    # query_graph("project 1",my_base64_jpgData)
    time_end = time.time()
    # print("Time taken to run maketermgraph: ", time_end - time_start)
    return buf

# improve
def addTable2TotalRowAndColoumn(pretable2, authors):
    # perluotomasi
    time_start = time.time()
    lenauthor = len(authors)

    sumrow = []
    sumcol = [0] * len(authors)

    for i, row in enumerate(pretable2):
        row_sum = 0
        for j, val in enumerate(row):
            row_sum += val
            sumcol[j] += val
        sumrow.append(row_sum)
    
    # print("p1p9(sumrow)")
    # print(sumrow)
    # print("p9p1(sumcol)")
    # print(sumcol)
    for x in range(lenauthor):
        pretable2[x].append(sumrow[x])
    pretable2.append(sumcol)
    # print(pretable2)
    print("Tabel 2: Add Total Row & Col (TABLE II. AUTHOR ADJACENT MATRIX OF 1994 PUBLICATION)")
    table2 = pd.DataFrame(pretable2)
    print(table2)
    time_end = time.time()
    # print("time addTable2TotalRowAndColoumn: "+str(time_end-time_start))
    return pretable2

def makeNewAdjMatrix(pretable3, lenauthor):
    # perluotomasi
    time_start = time.time()
    for x in range(lenauthor):
        for y in range(lenauthor):
            if pretable3[lenauthor][y] == 0:
                # print("nilaiku="+str(pretable3[x][y]))
                pretable3[x][y] = 1/lenauthor
            else:
                # print("nilaiku="+str(pretable3[x][y]))
                pretable3[x][y] = pretable3[x][y]/pretable3[lenauthor][y]
    table3 = pd.DataFrame(pretable3)
    print("Tabel pre III: Wij")
    print(table3)
    time_end = time.time()
    # print("time makeNewAdjMatrix: "+str(time_end-time_start))
    return pretable3

def rank(pretable3, author, name):
    # perluotomasi
    date_start = time.time()
    lenauthor = len(author)
    d = 0.850466963
    table4 = []
    row = []
    for x in range(lenauthor):
        row.append(1/lenauthor)
    table4.append(row)
    time_1 = time.time()
    for y in range(100):
        rowbaru = []
        for x in range(lenauthor):
            nilai = (1-d)+d * \
                np.matmul(pretable3[x][0:lenauthor], row[0:lenauthor])
            rowbaru.append(nilai)
        table4.append(rowbaru)
        selisih = abs(np.array(row)-np.array(rowbaru))
        ns = max(selisih)
        if ns < 0.001:
            # print("y="+str(y))
            break
        # print(ns)
        row = rowbaru
    time_2 = time.time()-time_1
    print("time of rank loop: "+str(time_2))
    rank = [sorted(row, reverse=True).index(x) for x in row]
    rank = [x + 1 for x in rank]
    table4.append(rank)
    table5 = pd.DataFrame(table4)
    print("Tabel 3: Ranking (TABLE III. S(VI)7$1'Ǽ_T OF AUTHOR-TERM GRAPH.)")
    print(table5.T)

    json_data = json.dumps({"author": author, "ranks": rank})
    # query_rank("project 1",json_data)
    date_end = time.time()
    print("time of rank function: "+str(date_end-date_start))
    return table4, rank,rowbaru


@application.route('/data/<type>/<name>', methods=['GET', 'POST'])
def data(type, name):
    if request.method == 'POST' or request.method == 'GET':
        start_time = time.time()
        if request.method == 'POST':
            table = getData(request.get_json()["data"])
        elif request.method == 'GET':
            table = getData()

        print("Tabel 1")
        title = ['Article-ID', 'Terms in Title and Keywords',
                 'Terms Found in Abstracts', 'Publication Year', 'Authors', 'References']
        print(title)
        # print(tabulate(table))

    # pair ArticleId,Author,& References & author
        pairs, authors, articles,initial_articles_pair ,title_articles_pair,initial_author_pair,nation_author_pair = getArticleIdAuthorReferencesAndAuthor(table)

        # for i in pairs:
        #     print(i)
        #     print("\n")
        # for y in authors:
        #     print(y)
        #     print("\n")

        # pasangan yang memungkinkan antara 2 penulis
        if type == "article":
            input_author_article = articles
        elif type == "author":
            input_author_article = authors
        author_matrix = author_matrixs(input_author_article)

    # ambil data untuk tabel 2(step 1)
        author_matrix_and_relation = getTable2Data(pairs, author_matrix, type)

        # for x in author_matrix_and_relation:
        #     print(x)
        # return author_matrix_and_relation

    # errornyadisini
        table2, raw_table2 = makeTable2(author_matrix_and_relation, input_author_article)
        # add total coloum & row in table 2
        raw_table2WithRowCol = addTable2TotalRowAndColoumn(raw_table2, input_author_article)
        # makeNewAdjMatrix
        newAdjMatrixs = makeNewAdjMatrix(raw_table2WithRowCol, len(input_author_article))
        # rank author
        table, author_rank,last_author_rank = rank(newAdjMatrixs, input_author_article, name)

        try:
            outer_author = request.get_json()["outer"]
            top_author_rank = request.get_json()["author-rank"]
        except:
            outer_author = 0
            top_author_rank = 20

        initial_articles_pair_search={}
        count=0
        for j in initial_articles_pair:
            initial_articles_pair_search[j]=count
            count+=1

        initial_author_pair_search={}
        count=0
        for j in initial_author_pair:
            initial_author_pair_search[j]=count
            count+=1

        if name == "graph":
            # Make Term Graph
            output = makeTermGraph(
                input_author_article, author_matrix_and_relation, last_author_rank, outer_author, top_author_rank)
            output.seek(0)
            my_base64_jpgData = base64.b64encode(output.read())
            if request.method == 'GET':
                end_time = time.time()
                total_time = end_time - start_time
                print(
                    "Waktu eksekusi program: {:.2f} detik".format(total_time))
                return Response(output.getvalue(), mimetype='image/png')
            else:
                end_time = time.time()
                total_time = end_time - start_time
                print(
                    "Waktu eksekusi program: {:.2f} detik".format(total_time))
                return my_base64_jpgData
        elif name == "rank":
            title_nation_of_the_article = []
            for i in input_author_article:
                if type == "article":
                    if i in initial_articles_pair:
                        title_nation_of_the_article.append(title_articles_pair[initial_articles_pair_search[i]])
                    else:
                        # bukan penulis pertama
                        title_nation_of_the_article.append("None")
                elif type == "author":
                    if i in initial_author_pair:
                        title_nation_of_the_article.append(nation_author_pair[initial_author_pair_search[i]])
                    else:
                        # bukan penulis pertama
                        title_nation_of_the_article.append("None")
            tmp = [input_author_article, [table, author_rank]]
            if type == "article" or type == "author":
                tmp.append(title_nation_of_the_article)
            end_time = time.time()
            total_time = end_time - start_time
            print("Waktu eksekusi program: {:.2f} detik".format(total_time))
            return tmp
        
        elif name == "rankgraph":
            title_nation_of_the_article = []
            for i in input_author_article:
                if type == "article":
                    if i in initial_articles_pair:
                        title_nation_of_the_article.append(title_articles_pair[initial_articles_pair_search[i]])
                    else:
                        # bukan penulis pertama
                        title_nation_of_the_article.append("None")
                elif type == "author":
                    if i in initial_author_pair:
                        title_nation_of_the_article.append(nation_author_pair[initial_author_pair_search[i]])
                    else:
                        # bukan penulis pertama
                        title_nation_of_the_article.append("None")

            tmp = {'authors':input_author_article, 'ranks':author_rank,'title':title_nation_of_the_article,'nodes_strength':last_author_rank}
            tmp=json.dumps(tmp)
            tmp_dict = json.loads(tmp)
            end_time = time.time()
            total_time = end_time - start_time
            print("Waktu eksekusi program: {:.2f} detik".format(total_time))
            return tmp_dict
        elif name == "rankgraphimage":
            title_nation_of_the_article = []
            for i in input_author_article:
                if type == "article":
                    if i in initial_articles_pair:
                        title_nation_of_the_article.append(title_articles_pair[initial_articles_pair_search[i]])
                    else:
                        # bukan penulis pertama
                        title_nation_of_the_article.append("None")
                elif type == "author":
                    if i in initial_author_pair:
                        title_nation_of_the_article.append(nation_author_pair[initial_author_pair_search[i]])
                    else:
                        # bukan penulis pertama
                        title_nation_of_the_article.append("None")

            tmp = {'authors':input_author_article, 'ranks':author_rank,'title':title_nation_of_the_article,'nodes_strength':last_author_rank}
            tmp=json.dumps(tmp)
            # Make Term Graph
            output = makeTermGraph(input_author_article, author_matrix_and_relation, last_author_rank, outer_author, top_author_rank)
            output.seek(0)
            my_base64_jpgData = base64.b64encode(output.read())
            my_base64_jpgData=my_base64_jpgData.decode("utf-8")
            tmp_dict = json.loads(tmp)
            tmp_dict['graph']=my_base64_jpgData

            end_time = time.time()
            total_time = end_time - start_time
            print("Waktu eksekusi program: {:.2f} detik".format(total_time))
            return tmp_dict

@application.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

if __name__ == "__main__":
    application.run(host='0.0.0.0')
