from csrankings import *

def parseDBLP(facultydict):
    authlogs = {}
    interestingauthors = {}
    authorscores = {}
    authorscoresAdjusted = {}
    coauthors = {}
    papersWritten = {}
    counter = 0
    
    with open('dblp.xml', mode='r') as f:
        
    # with gzip.open('dblp.xml.gz') as f:

        oldnode = None
        
        for (event, node) in ElementTree.iterparse(f, events=['start', 'end']):

            if (oldnode is not None):
                oldnode.clear()
            oldnode = node
            
            foundArticle = False
            inRange = False
            authorsOnPaper = 0
            authorName = ""
            confname = ""
            year = -1
            
            if (node.tag == 'inproceedings' or node.tag == 'article'):
                
                # First, check if this is one of the conferences we are looking for.
                
                for child in node:
                    if (child.tag == 'booktitle' or child.tag == 'journal'):
                        if (child.text in confdict):
                            foundArticle = True
                            confname = child.text
                        break

                if (not foundArticle):
                    # Nope.
                    continue

                # It's a booktitle or journal, and it's one of our conferences.

                # Check that dates are in the specified range.
                
                for child in node:
                    if (child.tag == 'year'): #  and type(child.text) is str):
                        year = int(child.text)
                        if ((year >= startyear) and (year <= endyear)):
                            inRange = True
                        break

                if (not inRange):
                    # Out of range.
                    continue

                # Now, count up how many faculty from our list are on this paper.

                foundOneInDict = False
                for child in node:
                    if (child.tag == 'author'):
                        authorName = child.text
                        authorName = authorName.strip()
                        authorsOnPaper += 1
                        if (authorName in facultydict):
                            foundOneInDict = True

                if (not foundOneInDict):
                    # No authors from our list.
                    continue

                # Count the number of pages. It needs to exceed our threshold to be considered.
                pageCount = -1
                for child in node:
                    if (child.tag == 'pages'):
                        pageCount = pagecount(child.text)

                tooFewPages = False
                if ((pageCount != -1) and (pageCount < pageCountThreshold)):
                    tooFewPages = True
                    if ((pageCount == 0) and ((confname == 'SC') or (confname == 'SIGSOFT FSE') or (confname == 'PLDI') or (confname == 'ACM Trans. Graph.'))):
                        tooFewPages = False
                    # SPECIAL CASE FOR conferences that have incorrect entries (as of 6/22/2016).
                    # Only skip papers with a very small paper count,
                    # but above 1. Why?
                    # DBLP has real papers with incorrect page counts
                    # - usually a truncated single page. -1 means no
                    # pages found at all => some problem with journal
                    # entries in DBLP.
                    # print "Skipping article with "+str(pageCount)+" pages."

                if ((confname == 'ASE') and (pageCount <= 6)):
                    tooFewPages = True
                    
                if (tooFewPages):
                    continue

                # If we got here, we have a winner.
                
                areaname = confdict[confname]
                for child in node:
                    if (child.tag == 'author'):
                        authorName = child.text
                        authorName = authorName.strip()
                        if (authorName in facultydict):
                            # print "here we go",authorName, confname, authorsOnPaper, year
                            if (generateLog):
                                logstring = authorName.encode('utf-8') + " ; " + confname + " " + str(year)
                                tmplist = authlogs.get(authorName,[])
                                tmplist.append(logstring)
                                authlogs[authorName] = tmplist
                            interestingauthors[authorName] = interestingauthors.get(authorName,0) + 1
                            authorscores[(authorName, areaname, year)] = authorscores.get((authorName, areaname, year), 0) + 1.0
                            authorscoresAdjusted[(authorName, areaname, year)] = authorscoresAdjusted.get((authorName, areaname, year), 0) + 1.0 / authorsOnPaper
                          
  
            
    if (generateLog):
        return (interestingauthors, authorscores, authorscoresAdjusted, authlogs)
    else:
        return (interestingauthors, authorscores, authorscoresAdjusted)


facultydict = csv2dict_str_str('faculty-affiliations.csv')

if (generateLog):
    (intauthors_gl, authscores_gl, authscoresAdjusted_gl, authlog_gl) = parseDBLP(facultydict)
else:
    (intauthors_gl, authscores_gl, authscoresAdjusted_gl) = parseDBLP(facultydict)

f = open('generated-author-info.csv','w')
f.write('"name","dept","area","count","adjustedcount","year"\n')
for k, v in intauthors_gl.items():
    #print k, "@", v
    if (v >= 1):
        for area in arealist:
            for year in range(startyear,endyear + 1):
                if (authscores_gl.has_key((k, area,year))):
                    count = authscores_gl.get((k,area,year))
                    countAdjusted = authscoresAdjusted_gl.get((k,area,year))
                    f.write(k.encode('utf-8'))
                    f.write(',')
                    f.write((facultydict[k]).encode('utf-8'))
                    f.write(',')
                    f.write(area)
                    f.write(',')
                    f.write(str(count))
                    f.write(',')
                    f.write(str(countAdjusted))
                    f.write(',')
                    f.write(str(year))
                    f.write('\n')
f.close()    


if (generateLog):
    f = open('rankings-all.log','w')
    for v, l in authlog_gl.items():
        if intauthors_gl.has_key(v):
            if (intauthors_gl[v] >= 1):
                f.write("Papers for " + v.encode('utf-8') + ', ' + (facultydict[v]).encode('utf-8') + "\n")
                for logstring in l:
                    f.write(logstring)
                    f.write('\n')
            f.write('\n')
    f.close()



