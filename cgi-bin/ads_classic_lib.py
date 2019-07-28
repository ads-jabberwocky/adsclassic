#!/usr/bin/env python
import sys, os, datetime, json, requests
if sys.version_info[0] == 2:
    from urllib import urlencode  # python2
else:
    from urllib.parse import urlencode  # python3

# you need to set the environment variable ADS_TOKEN, or modify the code below to assign it explicitly
token = os.environ['ADS_TOKEN']

now   = datetime.datetime.now()
dburl = 'https://api.adsabs.harvard.edu/v1/search/query'
style = '''<style type="text/css">
a:link {color: #0000ff}
a.oa:link {color: #00a000}
a:visited {color: #4000a0}
a.oa:visited {color: #006666}
a:hover {color: #ff0000}
a.oa:hover {color: #cc33cc}
td {vertical-align: top}
th {text-align: left}
span.h {visibility: hidden}
p.q {color: #a0a0a0}
</style>
'''

linkletters = 'A EFGX D RC SNH'
linktypes = dict(
    A='ABSTRACT',
    E='EJOURNAL',
    F='ARTICLE',
    G='GIF',
    X='PREPRINT',
    D='DATA',
    R='REFERENCES',
    C='CITATIONS',
    S='SIMBAD',
    N='NED',
    H='SPIRES')

sorttypes = dict(
    SCORE      = 'score desc',
    CITATIONS  = 'citation_count desc',
    AUTHOR     = 'first_author asc',
    AUTHOR_CNT = 'author_count asc',
    NDATE      = 'date desc',
    ODATE      = 'date asc')


if sys.version_info[0]==2:
    def udecode(x):  # string to unicode
        if isinstance(x, str): return x.decode('utf-8')
        else: return x
    def uencode(x):  # unicode to string
        if isinstance(x, unicode): return x.encode('utf-8')
        else: return x
else:  # in python 3, str already means unicode
    udecode = lambda x: x
    uencode = lambda x: x


def runQuery(query, sort='NDATE', start=0, num_items=2000, full=False):
    '''Query the ADS API
    '''
    if query == '':
        raise ValueError('Empty query')
    fields = 'bibcode,author,title,abstract,pubdate,citation_count,reference,links_data,esources,score'
    if full:
        fields += ',pub_raw,keyword,doi,aff'
    params = dict(q=query, start=start, fl=fields, rows=num_items)
    if sort in sorttypes:
        params['sort'] = sorttypes[sort]
    req = requests.get(dburl, params=params, headers=dict(Authorization='Bearer ' + token))
    result = req.json()
    if 'error' in result:
        raise ValueError(result['error']['msg'])
    elif not 'response' in result:
        raise ValueError(str(result))
    data   = result['response']
    header = req.headers
    data['remaining'] = header['X-RateLimit-Remaining']
    data['resettime'] = datetime.datetime.fromtimestamp(float(header['X-RateLimit-Reset'])) - now
    data['querytime'] = result['responseHeader']['QTime']
    return data


def printSummary(indx, item, sort=None):
    '''Print a row in the summary table: brief author list, title, date, links to data sources.
    This table is produced either by a author/title/abstract query, or a reference/citation query.
    '''
    if 'author' in item:
        author  = '; '.join(item['author'][:10])
        if len(item['author'])>10:
            author += '; <font color="red">and %i coauthors</font>' % (len(item['author'])-10)
    else: author = 'Anonymous'
    title   = ''.join(item['title']) if 'title' in item else 'Untitled'
    bibcode = item['bibcode']
    date    = item['pubdate'][5:7]+'/'+item['pubdate'][0:4] if 'pubdate' in item else '????/??'
    adslink = '<a href="http://adsabs.harvard.edu/cgi-bin/nph-data_query?bibcode=' + bibcode + '&link_type='
    loclink = '<a href="/cgi-bin/nph-data_query?bibcode=' + bibcode + '&link_type='
    links = ['<span class="h">' + l + '</span>&nbsp;&nbsp;' for l in linkletters]
    def addlink(letter, ac='', ct=None, link=None):
        links[linkletters.find(letter)] = link + linktypes[letter] + '"' + ac + \
            (' title="' + str(ct) + '"' if ct is not None else '') + '>' + letter + '</a>&nbsp;&nbsp;'
    if 'abstract' in item:
        addlink('A', link=loclink)
    if 'citation_count' in item and item['citation_count']>0:
        addlink('C', ct=item['citation_count'], link=loclink)
    if 'reference' in item:
        addlink('R', ct=len(item['reference']), link=loclink)
    if 'links_data' in item:
        for lida in item['links_data']:
            ld = json.loads(lida)
            ac = ' class="oa"' if 'access' in ld and ld['access'] == 'open' else ''
            lt = ld['type'] if 'type' in ld else None
            ct = ld['instances'] if 'instances' in ld else None
            if lt == 'electr':    addlink('E', ac, link=adslink)
            if lt == 'pdf' or lt == 'postscript': addlink('F', ac, link=adslink)
            if lt == 'gif':       addlink('G', ac, link=adslink)
            if lt == 'preprint':  addlink('X', ac, link=adslink)
            if lt == 'data':      addlink('D', ac, ct, link=adslink)
            if lt == 'simbad':    addlink('S', ac, ct, link=adslink)
            if lt == 'ned':       addlink('N', ac, ct, link=adslink)
            if lt == 'spires':    addlink('H', ac, link=adslink)
    if 'esources' in item:
        if 'ADS_PDF'  in item['esources']: addlink('F', ' class="oa"', link=adslink)
        if 'ADS_SCAN' in item['esources']: addlink('G', ' class="oa"', link=adslink)
    if   sort == 'CITATIONS' :
        score = str(item['citation_count']) if 'citation_count' in item else '0'
    elif sort == 'AUTHOR_CNT':
        score = str(len(item['author'])) if 'author' in item else '0'
    elif sort == 'SCORE':
        score = '%.3f' % item['score'] if 'score' in item else '0.000'
    else: score = '0.000'

    return '''<tr><td>%i</td> <td><input type="checkbox" name="bibcode" value="%s" disabled>&nbsp;<a href="/abs/%s">%s</a></td> <td>%s</td> <td>%s</td> <td>%s</td></tr>
<tr><td></td> <td>%s</td> <td colspan=3>%s</td></tr>
<tr><td colspan=6><hr></td></tr>''' % (indx+1, bibcode, bibcode, bibcode, score, date, ''.join(links), author, title)


def printAbstract(item):
    '''Print the abstract and associated data links (arxiv, pdf, online data, references, citations)
    '''
    aquery  = lambda a: '<a href="/cgi-bin/nph-abs_connect?' + urlencode([('author', a.encode('utf-8'))]) + '">' + a + '</a>'
    author  = '; '.join([aquery(a) for a in item['author'] ]) if 'author' in item else 'Anonymous'
    title   = ''.join(item['title']) if 'title' in item else 'Untitled'
    date    = item['pubdate'][5:7]+'/'+item['pubdate'][0:4] if 'pubdate' in item else '????/??'
    bibcode = item['bibcode']
    adslink = '<a href="http://adsabs.harvard.edu/cgi-bin/nph-data_query?bibcode=' + bibcode + '&link_type='
    loclink = '<a href="/cgi-bin/nph-data_query?bibcode=' + bibcode + '&link_type='
    result  = '<hr><dl>\n'
    links   = [''] * len(linkletters)
    def addlink(letter, text, ac='', ct=None, link=None):
        links[linkletters.find(letter)] = '<dt><b>' + link + linktypes[letter] + '"' + ac + \
            '>' + text + (' ('+str(ct)+')' if ct is not None else '') + '</a></b><br>'
    def addarxiv(url):
        links[linkletters.find('X')] = '<dt><b><a href="' + url + \
            '" class="oa">arXiv e-print</a></b> (' + url[url.find('arxiv.org/abs/')+14:] + ')<br>'
    if 'links_data' in item:
        for lida in item['links_data']:
            ld = json.loads(lida)
            ac = ' class="oa"' if 'access' in ld and ld['access'] == 'open' else ''
            lt = ld['type'] if 'type' in ld else None
            ct = ld['instances'] if 'instances' in ld and ld['instances']!='' else None
            if lt == 'electr':    addlink('E', 'Electronic on-line article (HTML)', ac, link=adslink)
            if lt == 'pdf' or lt == 'postscript':  addlink('F', 'Full article (PDF/Postscript)', ac, link=adslink)
            if lt == 'gif':       addlink('G', 'Scanned article (GIF)', ac, link=adslink)
            if lt == 'preprint':  addarxiv(ld['url'])
            if lt == 'data':      addlink('D', 'On-line data', ac, ct, link=adslink)
            if lt == 'simbad':    addlink('S', 'SIMBAD objects', ac, ct, link=adslink)
            if lt == 'ned':       addlink('N', 'NED objects', ac, ct, link=adslink)
            if lt == 'spires':    addlink('H', 'HEP/Spires information', ac, link=adslink)
    if 'esources' in item:
        if 'ADS_PDF'  in item['esources']: addlink('F', 'Full article (PDF/Postscript)', ' class="oa"', link=adslink)
        if 'ADS_SCAN' in item['esources']: addlink('G', 'Scanned article (GIF)', ' class="oa"', link=adslink)
    if 'reference' in item:
        addlink('R', 'References in the article', '', len(item['reference']), link=loclink)
    if 'citation_count' in item and int(item['citation_count'])>0:
        addlink('C', 'Citations to the article', '', item['citation_count'], link=loclink)
    result += ''.join(links)
    result += ('</dl><table>\n<tr><td><b>Title:</b></td><td>&nbsp;</td><td>' + title + '</td></tr>\n' +
        '<tr><td><b>Authors:</b></td><td>&nbsp;</td><td>' + author + '</td></tr>\n')
    if 'aff' in item:
        aff = []
        pair= len(item['aff']) == len(item['author'])
        for i, s in enumerate(item['aff']):
            if s!='-':
                aff.append( '<u>' + item['author'][i] + '</u>: ' + s if pair else s )
        if len(aff)>0:
            result += '<tr><td><b>Affiliation:</b></td><td>&nbsp;</td><td>' + '<br>'.join(aff) + '</td></tr>\n'
    if 'pub_raw' in item:
        result += '<tr><td><b>Publication:</b></td><td>&nbsp;</td><td>' + item['pub_raw'] + '</td></tr>\n'
    result += '<tr><td><b>Date:</b></td><td>&nbsp;</td><td>' + date + '</td></tr>\n'
    if 'keyword' in item:
        result += '<tr><td><b>Keywords:</b></td><td>&nbsp;</td><td>' + '; '.join(item['keyword']) + '</td></tr>\n'
    if 'doi' in item:
        doi = item['doi']
        doitext = '; '.join(['<a href="https://dx.doi.org/%s">%s</a>' % s for s in zip(doi,doi)])
        result += '<tr><td><b>DOI:</b></td><td>&nbsp;</td><td>' + doitext + '</td></tr>\n'
    result += '<tr><td><b>ADS:</b></td><td>&nbsp;</td><td><a href="http://adsabs.harvard.edu/abs/' + bibcode + '">' + bibcode + \
        '</a>&nbsp; [<a href="http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=' + bibcode + \
        '&data_type=BIBTEX">Bibtex entry</a>]</td></tr>\n</table>\n'

    if 'abstract' in item:
        result += '<h3 align="center">Abstract</h3>\n' + item['abstract']
    else:
        result += 'Abstract not available'
    result += '<br>\n'
    return result


def printTable(data, start=0, sort=None):
    '''Print the entire table of summary data for many bibcodes
    '''
    result = []
    if data['numFound'] > len(data['docs']):
        result.append(('<p>Selected and retrieved <b>%i</b> documents, starting with number <b>%i</b>.' +
            ' Total number selected: <b>%i</b></p>') % (len(data['docs']), data['start']+1, data['numFound']))
    else:
        result.append('<p>Selected and retrieved <b>%i</b> documents.</p>' % data['numFound'])

    if   sort == 'CITATIONS' : score = 'Cites'
    elif sort == 'AUTHOR_CNT': score = 'Nr.Auth.'
    else: score = 'Score'
    result.append('''
<hr>
<table>
<tr><th>#</th> <th width="25%%">Bibcode</th> <th width="6%%">%s</th> <th width="9%%">Date</th> <th><a href="http://adsabs.harvard.edu/abs_doc/help_pages/results.html#available_items">List of Links</a></th></tr>
<tr><th></th> <th>Authors</th> <th colspan=2>Title</th> <th><a href="http://adsabs.harvard.edu/abs_doc/help_pages/results.html#access_links">Access Control Help</a></tr>
<tr><td colspan=5><hr></td></tr>
''' % score)

    for indx, item in enumerate(data['docs']):
        result.append(printSummary(indx+start, item, sort=sort))

    result.append('</table>\n')
    return ''.join(result)


def printHeader(title, header=''):
    '''Print the beginning of a HTML webpage
    '''
    return 'Content-type: text/html; charset=UTF-8\r\n\r\n' + '''<html>
<head>
<title>%s</title>
<link rel="icon" href="http://adsabs.harvard.edu/favicon.ico">
%s
</head>
<body>
<h3><a href="http://adsabs.harvard.edu/">SAO/NASA Astrophysics Data System (ADS)</a>&nbsp;
<a href="/abstract_service.html">(neo)Classical Astronomy Abstract Service</a></h3>
<h3>%s</h3>
''' % (title, style, header)


def printFooter(data, footer=''):
    '''Print the end of a HTML webpage
    '''
    dt = datetime.datetime.now()-now
    return '%s\n<p class="q">execution time: %.3f s, query time: %.3f s, ' \
        'remaining quota: %s requests in the next %dh:%02dm</p>\n</body>\n</html>\n' % \
        (footer, dt.seconds+1e-6*dt.microseconds, float(data['querytime'])*1e-3,
        data['remaining'], data['resettime'].seconds//3600, (data['resettime'].seconds%3600)//60)


if __name__ == '__main__':   # prevent calling this script directly -- output an empty page
    print('Content-type: text/plain\r\n\r\n')
