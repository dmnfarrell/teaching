# This script searches RIP.ie data for known names/addresses
# Damien Farell 2021

import sys
import pandas as pd
import difflib
import re
pd.set_option('display.width', 150)

def clean_name(txt):
    clean = re.sub(r"""[,.;@#?!&$']+ \ * """, " ", 
                   txt, flags=re.VERBOSE)
    clean = clean.strip()
    return clean

def find_word(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def find_match(x,r): 
    name = clean_name(x['name'])
    name = name.lower()
    if r.surname.lower() in name and find_word(r.firstname)(name): #r.firstname.lower() in name:        
        return True
    return False

def run_search(db, targets, keep=1):
    """Search rip.ie table for known persons"""
    
    print ('searching %s rows' %len(db))
    results = []
    for i,r in targets.iterrows():
        print (r.case_id,r.surname,r.firstname)
        A = r.address
        f = db.apply(lambda x: find_match(x,r),1)
        res = db[f].copy()   
        if len(res) == 0:
            print ('no names match')
            res=pd.DataFrame([(r.case_id,0,'NA')],columns=['case_id','year','id'])
            print (res)            
        elif len(res) == 1:
            print ('one unique hit')
            #res = res.iloc[0]
        else:
            #get best match address
            print ('found %s hits' %len(res))
            addresses=list(res.address)            
            #res['score']=res.apply(lambda x: fuzz.ratio(A, x.address),1)
            res['score']=res.apply(lambda x: difflib.SequenceMatcher(None, A, x.address).ratio(),1)
            res = res.sort_values('score',ascending=False)
            res = res[:keep]
            #res = res.iloc[0]
        res['case_id'] = r.case_id
        results.append(res)
    
    results = pd.concat(results).reset_index(drop=True)
    return results

if __name__ == "__main__":
    targetfile = sys.argv[1]
    searchfile = sys.argv[2]
    df = pd.read_pickle(searchfile)   
    targets = pd.read_csv(targetfile)
    results = run_search(df, targets, keep=1)
    results = targets.merge(results,on='case_id')
    print (results)
    results.to_csv('rip_search_results.csv',index=False)
